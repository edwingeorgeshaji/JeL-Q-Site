"""Readable terminal flow for the Phase 2 prototype."""
import json
import sys
from rich.table import Table
from rich import box
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from dispatch import ROOT
from resilience import DEFAULT,run,validate


def show_logo(console):
    console.print(Text('''
    ██████╗         ███████╗ ██╗ ████████╗ ███████╗
   ██╔═══██╗        ██╔════╝ ██║ ╚══██╔══╝ ██╔════╝
   ██║   ██║ █████╗ ███████╗ ██║    ██║    █████╗
   ██║▄▄ ██║ ╚════╝ ╚════██║ ██║    ██║    ██╔══╝
   ╚██████╔╝        ███████║ ██║    ██║    ███████╗
    ╚══▀▀═╝         ╚══════╝ ╚═╝    ╚═╝    ╚══════╝
''',style='bold cyan'))
    console.print('[bold cyan]ENERGY RESERVE & RECOVERY[/]\n')


def display(console,report):
    width=min(console.width,120)
    def section(title,headers,rows):
        console.print('\n\n[bold cyan]'+title+'[/]\n')
        t=Table(box=box.MINIMAL,show_edge=False,width=width,padding=(1,3))
        for i,h in enumerate(headers):t.add_column(h,ratio=2 if i==0 else 3)
        for r in rows:t.add_row(*[str(x) for x in r])
        console.print(t)
        console.print()
    i=report['inputs']
    console.print('[yellow]SAVED REPLAY[/]' if report.get('replay') else '[green]FRESH EXPERIMENT[/]')
    console.print('\nTwo hours: normal operation, then the same grid outage for both plans.\n')
    section('1. Your inputs',['Input','Value'],[
        ('Normal demand',f"{i['demand']} kWh"),('Essential outage demand',f"{i['critical']} kWh"),
        ('Battery starting energy / output limit',f"{i['battery']} kWh / {i['power']} kW"),
        ('Emergency reserve',f"{i['reserve']} kWh"),('Outage solar / wind / diesel',f"{i['outage_solar']} / {i['outage_wind']} / {i['outage_diesel']} kWh"),
        ('Grid during outage','0 kWh')])
    a,b=report['plans']
    section('2. Classical exact plans / normal-hour allocation',['Source',a['name'],b['name']],[(name,*[f"{(r['exact'] or {}).get('sources_kwh',{}).get(name,0)} kWh" if r['exact'] else 'INFEASIBLE' for r in [a,b]]) for name in ['Solar','Wind','Battery','Grid import','Diesel']])
    section('3. The price of protection',['Metric',a['name'],b['name']],[(label,*[f(r) for r in [a,b]]) for label,f in [
        ('Normal-hour cost',lambda r:f"INR {r['exact']['cost_inr']:.0f}" if r['exact'] else 'Infeasible'),
        ('Battery carried into outage',lambda r:f"{r['outage']['remaining_before']} kWh" if r['outage'] else 'No plan')]])
    if a['exact'] and b['exact']:
        console.print(f"\nExtra normal-hour cost to protect the reserve: [bold]INR {b['exact']['cost_inr']-a['exact']['cost_inr']:.0f}[/]\n")
        maximum=max(a['exact']['cost_inr'],b['exact']['cost_inr'],1)
        console.print('[dim]Normal-hour bill / shorter bar costs less[/]\n')
        chart_width=max(8,min(30,console.width-44))
        for r in [a,b]:
            amount=round(chart_width*r['exact']['cost_inr']/maximum)
            line=Text(f"{r['name']:<18} │ ")
            line.append('█'*amount+' '*(chart_width-amount),style='cyan' if r is b else 'blue')
            line.append(f" │ INR {r['exact']['cost_inr']:.0f}")
            console.print(line)
            console.print()
    console.print('\n\n[bold cyan]4. Outage test / essential energy served[/]\n')
    for row in [a,b]:
        o=row['outage']
        if o is None:console.print(row['name']+': no feasible normal-hour plan');continue
        bar_width=max(8,min(30,console.width-56))
        n=round(bar_width*o['served']/max(i['critical'],1))
        line=Text(f"{row['name']:<18} │ ")
        line.append('█'*n+'░'*(bar_width-n),style='green' if not o['shortfall'] else 'yellow')
        line.append(f" │ {o['served']} / {i['critical']} kWh")
        console.print(line)
        console.print(f"\n  Shortage {o['shortfall']} kWh\n  Outage cost INR {o['cost_inr']:.0f}\n  Battery left {o['remaining_after']} kWh\n")
    section('5. Quantum versus classical / normal-hour dispatch',
            ['Plan / seed','Gap INR','Valid %','Optimal %','Time'],[
        (f"{'Cost' if r is a else 'Ready'}/{t['seed']}",t['gap'] if t['gap'] is not None else 'No sample',f"{t['feasible_shots']/t['shots']:.1%}",f"{t['optimal_shots']/t['shots']:.1%}",f"{t['seconds']:.2f}s") for r in [a,b] for t in r['trials']])
    console.print('Gap = best valid measured cost minus exact classical minimum.\n\nEvery trial uses 2,048 shots. Qiskit runs every training evaluation.\nThe classical optimizer tunes circuit angles. No speed advantage is claimed.\n')
    section('Classical search time / excludes shared problem construction',['Plan','Exact selection time'],[(r['name'],f"{r['exact_seconds']*1000:.3f} ms") for r in [a,b]])
    for r in [a,b]:
        if r['trials']:
            t=r['trials'][0];o=t['outage']
            console.print(f"{r['name']}: seed {t['seed']} measured plan outage coverage = "+(f"{o['served']}/{i['critical']} kWh" if o else 'no valid sample')+f"\n{t['qubits']} qubits; optimizer converged: {t['optimizer_success']}\n")
    section('6. Verified recovery / classical search',['Plan','Extra starting battery energy','Evidence'],[(r['name'],str(r['recovery']['added_kwh'])+' kWh' if r['recovery']['added_kwh'] is not None else 'No tested fix',f"{len(r['recovery']['attempts'])} tested increments; power limit unchanged") for r in [a,b]])
    console.print('Recovery re-solves normal dispatch and outage service for each 10 kWh increment up to +100 kWh.\n\nIt does not price new battery hardware or prove a globally cheapest infrastructure change.\n')
    console.print('\n[dim]Synthetic data. One specified outage, no charging or network physics. Raw inputs, counts, angles and recovery checks: results/resilience.json[/]')


def simple_results(console,report):
    i=report['inputs']; plans=report['plans']
    console.print('[yellow]Saved results[/]' if report.get('replay') else '[green]New simulation[/]')
    console.print('\n[bold cyan]YOUR SITUATION[/]\n')
    console.print(f"  Normal hour: {i['demand']} kWh needed\n\n  Power cut: {i['critical']} kWh needed for essential services\n\n  Battery starts with {i['battery']} kWh stored\n")
    console.print(f"[dim]During the power cut: solar {i['outage_solar']}, wind {i['outage_wind']}, generator {i['outage_diesel']} kWh available.\nBattery delivery limit: {i['power']} kWh per hour. No charging between hours.[/]\n")
    t=Table(box=box.MINIMAL,show_edge=False,padding=(1,2),width=min(console.width,100))
    t.add_column('Plan',ratio=3);t.add_column('Cost before power cut',ratio=2);t.add_column('During power cut',ratio=3)
    for r in plans:
        o=r['outage']
        label='Spend less now' if r['reserve']==0 else 'Save battery for later'
        t.add_row(label,f"INR {r['exact']['cost_inr']:.0f}" if r['exact'] else 'Not possible',
                  f"{o['served']} of {i['critical']} kWh supplied\n"+('All essential energy supplied' if o['shortfall']==0 else f"Short by {o['shortfall']} kWh") if o else 'No valid starting plan')
    console.print(t)
    console.print('\n[bold cyan]ENERGY PRICES AND COST CALCULATIONS[/]\n')
    console.print('Source costs are calculated from the energy allocation and the listed rate.\n')
    for index,r in enumerate(plans):
        console.print('\n[bold]'+('Spend less now' if index==0 else 'Save battery for later')+'[/]\n')
        costs=Table(box=box.MINIMAL,show_edge=False,padding=(1,2),width=min(console.width,110))
        for name in ['Source','Energy','Rate / 10 kWh','Cost calculation / INR']:
            costs.add_column(name,ratio=2 if name=='Cost calculation / INR' else 1)
        rates={s['name']:s['cost_per_block_inr'] for s in r['config']['sources']}
        # An unavailable battery has no encoded variable, but its rate is still shown.
        rates.setdefault('Battery',25)
        plan=r['exact']
        for name in ['Solar','Wind','Battery','Grid import','Diesel']:
            rate=rates[name]
            energy=plan['sources_kwh'].get(name,0) if plan else None
            costs.add_row(name,f'{energy} kWh' if energy is not None else '-',
                          f'INR {rate:g}',
                          f'{energy/10:g} x {rate:g} = {energy/10*rate:g}' if energy is not None else 'No feasible plan')
        if plan:
            costs.add_row('TOTAL',f"{plan['supply_kwh']:g} kWh",'',f"INR {plan['cost_inr']:g}")
        console.print(costs)
    console.print('\n[dim]These are illustrative normal-hour operating costs, excluding equipment purchase and installation. The allocations above are the exact classical plans; quantum samples are compared below.[/]\n')
    console.print('\n[bold cyan]WHICH PLAN KEEPS ESSENTIAL SERVICES POWERED?[/]\n')
    size=max(8,min(30,console.width-45))
    for index,r in enumerate(plans):
        o=r['outage']
        if not o:continue
        filled=round(size*o['served']/max(i['critical'],1))
        line=Text(f"  {'Spend less now' if index==0 else 'Save for later':<18} ")
        line.append('█'*filled+'░'*(size-filled),style='green' if o['shortfall']==0 else 'yellow')
        line.append(f"  {o['served']}/{i['critical']} kWh")
        console.print(line);console.print()
    a,b=plans
    if a['exact'] and b['exact']:
        extra=b['exact']['cost_inr']-a['exact']['cost_inr']
        console.print(f"Saving battery costs INR {extra:.0f} extra before the power cut.\n")
    fix=a['recovery']['added_kwh']
    if fix is None:
        console.print('Adding stored energy alone did not fix the shortage in the tested range.\n')
    elif fix>0:
        console.print(f'Another tested option: start with {fix} kWh more battery energy.\nThis fixes the first plan in this example; buying that capacity is not priced.\n')
    else:
        console.print('The first plan already covers essential demand during this power cut.\n')
    trials=[t for r in plans for t in r['trials']]
    matches=sum(t['gap']==0 for t in trials)
    console.print('[bold cyan]QUANTUM CHECK[/]\n')
    console.print(f'{matches} of {len(trials)} simulated runs measured a valid allocation matching the exact classical cost.\n')
    console.print('[dim]We select the best valid measured sample. This does not show a speed advantage.\nSynthetic two-hour example. Complete measurements are saved in results/resilience.json.[/]')
    console.print('\nMore detail: python dashboard.py --advanced --cached\n')


def main(console,cached=False,interactive=False,seeds=(42,43,44),advanced=False):
    show_logo(console)
    if cached:
        path=ROOT/'results'/'resilience.json'
        if not path.exists():console.print('No Phase 2 replay yet. Run python dashboard.py --demo');return
        report=json.loads(path.read_text());report['replay']=True
    else:
        inputs=DEFAULT.copy()
        if interactive and not advanced:
            console.print('Compare electricity cost and battery backup during a power outage.\n')
            console.print('[bold]Select an option[/]\n\n  1. Run the example scenario\n\n  2. Enter your energy requirements\n')
            choice=Prompt.ask('Enter your choice',choices=['1','2'],default='1')
            if choice=='2':
                console.print('\nType a number, then press Enter. Press Enter alone to keep the example.\nEnergy is in kWh: a 1 kW appliance running for one hour uses 1 kWh.\n')
                for key,label in [('demand','1. How much electricity is needed during the normal hour?'),('critical','2. How much electricity must essential services receive during the outage hour?'),('battery','3. How much usable energy is stored in the battery at the start?')]:
                    while True:
                        console.print('\n'+label+'\n')
                        value=IntPrompt.ask('Enter energy in kWh',default=inputs[key])
                        cap=300 if key=='battery' else 200
                        if 0<=value<=cap and value%10==0:
                            inputs[key]=value;break
                        console.print(f'[yellow]Use 0, 10, 20, ... up to {cap}.[/]')
                inputs['reserve']=min(inputs['critical'],inputs['battery'])
                console.print(f"\nQ-Site will compare unrestricted battery use with a reserve of {inputs['reserve']} kWh.\n")
        if interactive and advanced:
            console.print('We plan one normal hour, then one hour without grid electricity.\n')
            console.print('[bold]Choose how to begin[/]\n\n  1. Shelter demo - use the example values\n\n  2. Custom inputs - enter your own values\n')
            choice=Prompt.ask('Your choice',choices=['1','2'],default='1')
            if choice=='1':
                console.print('\n[bold]Choose the outage conditions[/]\n\n  1. Grid fails; solar, wind and diesel remain available\n     Each can supply up to 30 kWh during the outage hour.\n\n  2. Grid fails; only the battery is available\n     Solar, wind and diesel supply nothing.\n')
                event=Prompt.ask('Your choice',choices=['1','2'],default='2')
                if event=='1':
                    inputs.update(outage_solar=30,outage_wind=30,outage_diesel=30)
            if choice=='2':
                labels=dict(demand='Normal demand (kWh)',critical='Essential outage demand (kWh)',battery='Starting battery energy (kWh, max 300)',power='Battery output limit (kW, max 30)',reserve='Reserve (kWh)',outage_solar='Outage solar energy (kWh, max 30)',outage_wind='Outage wind energy (kWh, max 30)',outage_diesel='Outage diesel energy (kWh, max 30)')
                explanations=dict(
                    demand='Total electricity needed during the first, normal hour. Example: 80 kWh.',
                    critical='Electricity essential services need during the following outage hour. Example: 30 kWh. This is not added to normal-hour demand.',
                    battery='Usable energy already stored before the normal hour begins. It carries forward; it does not refill between hours.',
                    power='Maximum battery delivery rate. A 30 kW limit allows at most 30 kWh during either one-hour interval, even with more energy stored.',
                    reserve='Energy the Emergency Ready plan must leave in the battery after the normal hour. Lowest Cost has no reserve rule. Reserve cannot exceed starting energy.',
                    outage_solar='Maximum solar energy available during the outage hour. Enter 0 for no sunlight.',
                    outage_wind='Maximum wind energy available during the outage hour. Enter 0 when wind is unavailable.',
                    outage_diesel='Maximum generator energy available during the outage hour. Enter 0 if the generator is unavailable.')
                console.print('\nEnergy uses kWh: a 1 kW appliance running for one hour uses 1 kWh.\nEnter multiples of 10. Press Enter to keep the value shown in brackets.\nNormal-hour solar, wind, grid and diesel each have a fixed 30 kWh limit.\nPrices are fixed illustrative values; the battery does not charge in this demo.\n')
                while True:
                    for index,(key,label) in enumerate(labels.items(),1):
                        console.print(f'\n[bold cyan]{index}. {label}[/]\n\n  '+explanations[key]+'\n')
                        inputs[key]=IntPrompt.ask('Enter value',default=inputs[key])
                    try:validate(inputs);break
                    except ValueError as e:console.print(f'[red]{e}. Please correct the inputs.[/]')
        with console.status('Solving plans and training Qiskit circuits…'):
            report=run(inputs,seeds)
    if advanced:display(console,report)
    else:simple_results(console,report)
    console.save_text(str(ROOT/'results'/'phase2_dashboard.txt'))

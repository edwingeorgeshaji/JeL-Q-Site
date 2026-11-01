"""JeL Q-Site terminal dashboard. Run: python dashboard.py"""
import argparse
import contextlib
import io
import json
import platform
import statistics
import time
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule

from dispatch import ROOT

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
console = Console(record=True)
COLORS = ['yellow','cyan','magenta','blue','red']


def table(title, columns):
    t = Table(title=title, expand=True, header_style='bold cyan', border_style='blue')
    for c in columns:
        t.add_column(c)
    return t


def bar(value, maximum, width=30, color='cyan'):
    filled = round(width*value/maximum) if maximum else 0
    return Text('█'*filled+'░'*(width-filled),style=color)


def trend(values, width=65):
    import numpy as np
    points = [min(chunk) for chunk in np.array_split(values,min(width,len(values)))]
    lo, hi = min(points),max(points)
    return ''.join('▁▂▃▄▅▆▇█'[min(7,int(7*(v-lo)/(hi-lo or 1)))] for v in points)


def show_scenario(r):
    console.print(Rule(r['scenario']['name'],style='cyan'))
    demand = r['scenario']['demand_kwh']
    if r['status']=='infeasible':
        console.print(Panel(f'[bold red]DEMAND CANNOT BE MET[/]\nDemand {demand} kWh exceeds the configured 150 kWh capacity.\nNo quantum allocation is claimed.',border_style='red'))
        return
    exact, quantum, greedy = r['exact'],r['best_feasible_sample'],r['greedy']
    console.print(Panel(f'[bold]Demand {demand} kWh   |   {r["qubits"]} qubits   |   {r["shots"]:,} shots[/]\nQiskit local simulation · p=3 · 3 optimizer starts · synthetic one-hour inputs',border_style='cyan'))
    t = table('Resource allocation / kWh',['Resource','Capacity','Exact','QAOA sample','Allocation chart'])
    for i,(name,value) in enumerate(exact['sources_kwh'].items()):
        q = quantum['sources_kwh'][name] if quantum else 0
        t.add_row(name,'30',str(value),str(q) if quantum else '—',bar(q,30,color=COLORS[i]))
    console.print(t)
    t = table('Classical vs quantum-assisted result',['Method','Cost / INR','Supply / kWh','Feasible','Solver time / ms'])
    for label,a,seconds in [('Exact enumeration',exact,r['exact_seconds']),('Classical merit order',greedy,r['greedy_seconds']),('QAOA best feasible sample',quantum,r['qaoa_seconds'])]:
        t.add_row(label,f'{a["cost_inr"]:.2f}' if a else '—',str(a['supply_kwh']) if a else '—',str(a['feasible']) if a else 'No sample',f'{seconds*1000:.3f}')
    console.print(t)
    console.print('[dim]Shared QUBO construction excluded from solver times; QAOA includes training, verification and sampling. Single-run timings are illustrative.[/]')
    optimal = sum(c for b,c in r['counts'].items() if int(b,2)==exact['state_index'])
    t = table('Measurement quality',['Metric','Observed','Share of 4,096 shots'])
    for label,count in [('Feasible',r['feasible_shots']),('Optimal allocation',optimal),('Demand violations',r['shots']-r['feasible_shots'])]:
        t.add_row(label,f'{count:,} ({count/r["shots"]:.2%})',bar(count,r['shots']))
    console.print(t)
    console.print(f'Best-sample cost gap: [bold green]{r["optimality_gap_inr"]} INR[/] | Uniform probability of this unique optimum: {1/2**r["qubits"]:.3%}')
    mode=r['modal_sample']
    console.print(f'Most frequent state: {mode["bitstring"]} · supply {mode["supply_kwh"]} kWh · feasible {mode["feasible"]}')
    t=table('Most frequent measured bitstrings',['Bits (variable 0 at right)','Shots','Frequency'])
    maximum=max(r['counts'].values())
    for b,c in sorted(r['counts'].items(),key=lambda v:-v[1])[:8]:
        t.add_row(b,str(c),bar(c,maximum))
    console.print(t)
    console.print(Panel(Text(trend(r['history']),style='cyan'),title='Expected penalized energy / evaluation windows (lower is better)'))
    console.print(f'[dim]Each glyph is the minimum within an evaluation window; includes restart boundaries. {len(r["history"])} evaluations. Range {min(r["history"]):.1f}–{max(r["history"]):.1f} INR.[/]')
    console.print(f'Optimizer converged: {r["optimizer_success"]}. {r["optimizer_message"]}')


def large_scale():
    import numpy as np
    rows=[]
    console.print(Rule('Scale laboratory',style='magenta'))
    t=table('Measured classical dispatch / synthetic independent resources',['Sources','Demand / kWh','Cost / INR','Median ms','Demand met'])
    for n in [5,50,500,5000]:
        costs=np.resize(np.array([8.,12.,25.,55.,75.]),n)
        demand=int(n*3*.6)
        times=[]
        for _ in range(7):
            start=time.perf_counter()
            remaining=demand
            cost=0.
            for index in np.argsort(costs):
                amount=min(3,remaining)
                cost+=amount*costs[index]
                remaining-=amount
                if not remaining:
                    break
            times.append(time.perf_counter()-start)
        ms=statistics.median(times)*1000
        rows.append(dict(sources=n,demand_kwh=demand*10,cost_inr=cost,median_ms=ms,remaining_blocks=remaining))
        t.add_row(f'{n:,}',f'{demand*10:,}',f'{cost:,.0f}',f'{ms:.3f}',str(remaining==0))
    console.print(t)
    console.print('[dim]Seven repeats per size. Actual classical runs; merit order is exact for this linear model. No grid physics or coupling constraints.[/]')
    t=table('Statevector scaling / theoretical memory only',['Sources','Encoded qubits','Complex128 state memory','Quantum run?'])
    for n in [5,10,15,50,500,5000]:
        qubits=2*n
        if qubits<=60:
            memory=f'{16*2**qubits/2**30:,.3f} GiB'
        else:
            memory=f'~10^{(4+qubits)*.30103:.0f} bytes'
        t.add_row(str(n),str(qubits),memory,'Measured: 5 sources only' if n==5 else 'Not run; memory estimate')
    console.print(t)
    console.print(Panel('Classical merit order scales well for this model. Matching its cost on 5 sources demonstrates correctness, not quantum speedup.\n\nA larger quantum study would require bounded subproblems, richer dispatch constraints and measured solution-quality comparisons. The memory estimates describe classical statevector simulation, not QPU memory.',title='What the comparison supports',border_style='magenta'))
    return rows


def simple_view(rows):
    from rich import box
    layout_width=min(console.width,120)
    label_width=20
    value_width=12
    chart_width=max(8,layout_width-label_width-value_width-14)
    def chart_table(headers):
        # MINIMAL has continuous internal vertical rules and no outer frame.
        t=Table(box=box.MINIMAL,show_edge=False,show_header=True,
                padding=(0,2),pad_edge=True,collapse_padding=False,
                border_style='dim cyan',header_style='bold',width=layout_width)
        for i,heading in enumerate(headers):
            width=[label_width,chart_width,value_width][i]
            t.add_column(heading,width=width,min_width=width,max_width=width,
                         justify='right' if i==2 else 'left',no_wrap=True)
        t.add_row('','','')
        return t
    def print_chart(t):
        t.add_row('','','')
        console.print(t)
    heading = r'''
    ██████╗         ███████╗ ██╗ ████████╗ ███████╗
   ██╔═══██╗        ██╔════╝ ██║ ╚══██╔══╝ ██╔════╝
   ██║   ██║ █████╗ ███████╗ ██║    ██║    █████╗
   ██║▄▄ ██║ ╚════╝ ╚════██║ ██║    ██║    ██╔══╝
   ╚██████╔╝        ███████║ ██║    ██║    ███████╗
    ╚══▀▀═╝         ╚══════╝ ╚═╝    ╚═╝    ╚══════╝
'''
    console.print(Text(heading,style='bold cyan'))
    console.print('  Meet electricity demand at the lowest cost.',style='bold')
    console.print('  Qiskit simulation on this computer\n',style='dim')
    for r in rows:
        demand=r['scenario']['demand_kwh']
        console.print(Rule(r['scenario']['name']))
        if r['status']=='infeasible':
            console.print(f'[red]Demand: {demand} kWh | Available: 150 kWh | Shortage: {demand-150} kWh[/]')
            console.print('More energy capacity is needed.\n')
            continue
        q=r['best_feasible_sample']
        console.print(f'[bold]Electricity needed: {demand} kWh[/]')
        if q is None:
            console.print('[red]The simulation did not measure a valid allocation.[/]')
            continue
        console.print('\n[bold]Energy supplied by each source[/]  [dim](bar scale: 0–60 kWh)[/]')
        energy_table=chart_table(['Source','Energy chart','Supplied'])
        for name,value in q['sources_kwh'].items():
            blocks=round(chart_width*value/60)
            energy_table.add_row(name,Text('█'*blocks,style=COLORS[list(q['sources_kwh']).index(name)]),f'{value} kWh')
        print_chart(energy_table)
        console.print('\n[bold]Cost comparison[/]  [dim](shorter bar = lower cost)[/]')
        maximum=max(r['exact']['cost_inr'],q['cost_inr'],1)
        cost_table=chart_table(['Method','Cost chart','Cost'])
        for label,cost,color in [('Classical',r['exact']['cost_inr'],'blue'),('Quantum-assisted',q['cost_inr'],'cyan')]:
            blocks=round(chart_width*cost/maximum)
            cost_table.add_row(label,Text('█'*blocks,style=color),f'INR {cost:.0f}')
        print_chart(cost_table)
        console.print('\n[bold]Demand coverage[/]')
        coverage=chart_table(['Demand','Coverage chart','Energy'])
        coverage.add_row('Needed',Text('─'*chart_width,style='yellow'),f'{demand} kWh')
        blocks=round(chart_width*q['supply_kwh']/demand) if demand else 0
        coverage.add_row('Supplied',Text('█'*blocks,style='green'),f'{q["supply_kwh"]:.0f} kWh')
        print_chart(coverage)
        console.print()
        gap=r['optimality_gap_inr']
        console.print(f'[green]Demand met: {q["supply_kwh"]:.0f} / {demand} kWh.[/] '+('The costs match.' if gap==0 else f'Quantum sample costs INR {gap:.0f} more.'))
        console.print()
    console.print('[dim]Illustrative one-hour scenarios. Quantum result is selected from simulated measurements; matching cost does not establish a speed advantage.[/]')
    console.print('\n[cyan]Optional:[/] --details for technical charts | --scale for large-scale comparison')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cached',action='store_true',help='Display saved results without rerunning')
    parser.add_argument('--scenario',choices=['all','0','1','2'],default='all')
    parser.add_argument('--details',action='store_true',help='Show technical charts and measurements')
    parser.add_argument('--scale',action='store_true',help='Show large-scale classical benchmarks and memory estimates')
    parser.add_argument('--phase2',action='store_true',help='Show rubric evidence, live validation and quantum/classical metrics')
    parser.add_argument('--legacy',action='store_true',help='Original one-hour allocation dashboard')
    parser.add_argument('--demo',action='store_true',help='Run Phase 2 shelter preset without input prompts')
    parser.add_argument('--advanced',action='store_true',help='Detailed Phase 2 inputs, measurements and comparisons')
    parser.add_argument('--trials',type=int,choices=[1,3],default=3,help='Number of declared quantum seeds')
    args=parser.parse_args()
    if not args.legacy and not args.details and not args.scale:
        from resilience_ui import main as phase2_main
        phase2_main(console,cached=args.cached,interactive=sys.stdin.isatty() and not args.demo,
                    seeds=(42,) if args.trials==1 else (42,43,44),advanced=args.advanced)
        return
    if not args.cached:
        with console.status('Training QAOA and sampling verified Qiskit circuits…',spinner='dots'):
            from qiskit_local import main as run
            with contextlib.redirect_stdout(io.StringIO()):
                run()
    rows=json.loads((ROOT/'results'/'qiskit_local.json').read_text())
    selected=[r for i,r in enumerate(rows) if args.scenario=='all' or i==int(args.scenario)]
    if args.details:
        for r in selected:
            show_scenario(r)
    else:
        simple_view(selected)
    if args.scale:
        scaling=large_scale()
        (ROOT/'results'/'scaling.json').write_text(json.dumps(dict(machine=platform.platform(),benchmark=scaling),indent=2))
    if args.phase2:
        from phase2 import render_phase2
        render_phase2(console,rows,cached=args.cached)
    console.save_text(str(ROOT/'results'/'dashboard.txt'))


if __name__=='__main__':
    main()

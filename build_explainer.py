"""Build the plain-language Q-Site project explainer."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'/'pdf'
OUT.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyQ',fontName='Helvetica',fontSize=11,leading=16,spaceAfter=9,textColor=colors.HexColor('#243746')))
styles.add(ParagraphStyle(name='TitleQ',fontName='Helvetica-Bold',fontSize=30,leading=35,spaceAfter=16,textColor=colors.HexColor('#087f8c')))
styles.add(ParagraphStyle(name='SubQ',fontName='Helvetica-Bold',fontSize=13,leading=18,spaceBefore=9,spaceAfter=8,textColor=colors.HexColor('#087f8c')))
styles.add(ParagraphStyle(name='BulletQ',parent=styles['BodyQ'],leftIndent=13,firstLineIndent=-10,spaceAfter=6))
story=[]
def p(text): story.append(Paragraph(text,styles['BodyQ']))
def h(text): story.append(Paragraph(text,styles['SubQ']))
def b(text): story.append(Paragraph('- '+text,styles['BulletQ']))
def page(number,title,kicker):
    if story: story.append(PageBreak())
    story.append(Paragraph(f'{number:02d} / {kicker.upper()}',styles['SubQ']))
    story.append(Paragraph(title,styles['TitleQ']))
def table(headers,rows,widths=None):
    cell_style=ParagraphStyle(name='CellQ',parent=styles['BodyQ'],fontSize=10,leading=14,spaceAfter=5)
    content=[[Paragraph(str(c),cell_style) for c in row] for row in [headers]+rows]
    t=Table(content,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0f1f1')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(t); story.append(Spacer(1,12))

page(1,'Q-Site','A guide for everyone')
p('<b>Affordable energy today. Essential services protected tomorrow.</b>')
p('Q-Site is an energy-planning prototype. Its working version chooses how much electricity to take from available sources at the lowest modeled operating cost. Its updated direction adds emergency planning: decide what must stay powered, what can wait, and what change could fix a shortage.')
h('The problem in one sentence')
p('A site has limited electricity, several sources with different costs, and activities that need power. A useful plan must balance the bill with the consequences of losing power.')
h('Two stages - keep them separate')
b('<b>Working and tested:</b> a one-hour energy allocation model, local quantum-circuit simulation, classical comparisons, and a terminal dashboard.')
b('<b>Proposed extension:</b> multiple hours, essential-load priorities, flexible tasks, battery reserves, outage testing, and recovery recommendations. These have not yet been implemented or measured in this project.')
h('How to read this guide')
p('Pages 2-4 explain the problem and updated idea. Pages 5-9 explain the working mathematics, quantum method and results. Pages 10-13 cover use cases, existing tools, costs and scaling. Page 14 gives the demonstration and evidence checklist.')
p('<b>Phase 1 submission:</b> pages 15-19 define the revised hackathon scope, judging-rubric mapping, Sustainable Development Goal links, time-boxed build plan, quantum experiment and presentation. This bounded scope takes priority over the broader future roadmap.')
p('Prepared for Quantum Hack Day - Kochi. Team: JeL. Version: 1 November 2026. All example electricity prices are illustrative, not real tariffs. No new hardware result is claimed.')

page(2,'First, the everyday terms','Definitions')
table(['Term','Plain meaning'],[
('Energy','An amount of electricity used or supplied over time. We measure it in kilowatt-hours, written kWh. A 1-kilowatt appliance running for one hour uses 1 kWh.'),
('Power','The rate at which electricity is used or produced, measured in kilowatts, written kW. Power and energy are different; one hour at 30 kW supplies 30 kWh.'),
('Demand or load','Electricity needed by appliances, equipment or activities. A load can also mean the equipment itself.'),
('Capacity','A limit. A generator has a power limit; a battery has both a power limit and a stored-energy limit. The current one-hour model represents available energy only.'),
('Dispatch or allocation','The decision about how much each source should supply. Scheduling also decides when a task should run.'),
('Operating cost','The modeled money spent supplying electricity during operation. It is different from buying or installing equipment.'),
('Feasible plan','A plan that satisfies every rule in the model. Feasible does not automatically mean safe for a real electrical network.'),
('Optimization','Searching for the best permitted plan according to a chosen score, such as lowest cost.')],[120,371])
p('In this guide, INR means Indian rupees. A microgrid is a local group of electricity sources and users that can be coordinated; some microgrids can operate independently when the wider grid fails. Our software models planning decisions, not the electrical switching needed to disconnect a site safely.')

page(3,'Why cost alone is not enough','The updated idea')
p('An outage is a loss of grid electricity. A critical load is an activity whose interruption has serious consequences, such as medical refrigeration or emergency communications. Critical-load dispatch means allocating available energy to these essential activities first.')
p('Resilience means the ability to continue essential operation during a disruption and recover afterward. Outage resilience asks whether the available resources can support specified essential loads for a specified outage period. It is conditional on the inputs, not a promise that power will never fail.')
h('A simple reserve example - proposed behavior')
p('Suppose a battery begins with 30 kWh of usable energy. In the current 80 kWh example, the cheapest plan uses 20 kWh from it. That leaves 10 kWh. If later essential demand is 10 kW and no other source is available, that energy supports roughly one hour, assuming no losses and enough battery output power.')
p('If we require a 20 kWh emergency reserve, the battery may supply only 10 kWh now. Solar supplies 30, wind 30, battery 10 and grid imports 10 kWh. With our illustrative prices, that costs INR 140 instead of INR 110: INR 30 more to preserve another 10 kWh.')
b('The lowest-cost plan minimizes the immediate bill.')
b('The emergency-ready plan minimizes cost while respecting a reserve or an outage-service requirement.')
b('Neither is universally best. The user must specify how much protection matters and what conditions the plan must survive.')
p('This reserve calculation is an explanatory example. It has not yet been added to the application. Real endurance must account for changing loads, charging losses, equipment failures and battery output limits.')

page(4,'What the updated system should do','Proposed workflow')
p('A planning horizon is the future time period being planned, divided into intervals such as one-hour slots. A flexible task is an activity that may move within an allowed time window while still meeting its deadline.')
h('1. Ask for understandable inputs')
b('Enter essential loads, flexible tasks and their deadlines. For each source, enter available power, energy, cost and availability by time interval.')
b('Enter battery starting charge, storage size, charge/discharge power limits and efficiency. Efficiency is the fraction of input energy that remains useful after losses.')
h('2. Build two plans')
b('Lowest Cost: meet the stated service requirements at minimum modeled expense.')
b('Emergency Ready: meet the same requirements while preserving a specified reserve or surviving a stated set of outage scenarios.')
h('3. Let the user break the plan')
p('An interactive failure test lets a user remove grid supply, reduce solar, disable a generator or increase demand. Both plans must face the same disturbance and assumptions. The interface should show essential demand served, delayed tasks, battery energy and cost over time.')
h('4. Explain how to recover')
p('A recovery recommendation is a change that the model verifies by solving again. Search permitted changes, such as additional usable battery energy or postponing a nonessential task. Report the smallest successful change within those tested options, the unit used to compare changes, and any remaining violation. There may be no fix among the permitted options.')
p('The system is a decision-support prototype: a tool for understanding choices. It does not directly control electrical equipment. These four steps describe the target extension, not completed functionality.')

page(5,'What runs today','Inputs and boundaries')
p('The current prototype plans one hour using synthetic data: invented examples intended for repeatable demonstrations. A scenario is one particular set of inputs. Inputs currently come from scenarios.json; the terminal does not yet ask the user to enter them.')
table(['Source','Available energy','Cost / 10 kWh'],[('Solar','30 kWh','INR 8'),('Wind','30 kWh','INR 12'),('Battery','30 kWh','INR 25'),('Grid import','30 kWh','INR 55'),('Diesel','30 kWh','INR 75')],[173,159,159])
p('The three demand scenarios are 80, 120 and 160 kWh. Each source can supply 0, 10, 20 or 30 kWh. Total available energy is 150 kWh.')
h('What the prices mean')
p('Solar and wind prices are simplified assigned operating costs, not claims about actual market tariffs. Battery cost is a simplified discharge-use cost. Its energy is assumed to be stored before the modeled hour; charging purchase cost and losses are not separately modeled.')
h('What this model leaves out')
b('No battery charging or energy carry-over between hours. Scenarios are independent; each starts with the same available battery energy.')
b('No electrical network model, voltage analysis, transmission limits, fuel logistics, emissions objective or generator startup costs.')
b('No forecast, live weather feed, physical sensor connection or outage-resilience calculation.')
p('These limits make the prototype easy to reproduce and explain. A larger deployment requires a richer model and validated site data.')

page(6,'Turn energy choices into a score','QUBO explained')
p('A binary variable is a decision that can be only 0 or 1. A Quadratic Unconstrained Binary Optimization model, abbreviated QUBO, scores binary decisions using individual terms and pairs of decisions. Quadratic means terms involve at most two variables. Unconstrained means rules are represented inside the score as penalties.')
p('QUBO is a mathematical format. Classical algorithms can solve it too; it is not an exclusive language of quantum computers.')
h('Represent the supply')
p('Each source has two bits, a and b. Supply in 10 kWh blocks is a + 2b. The four settings 00, 01, 10 and 11 correspond to 0, 1, 2 and 3 blocks when decoded with the stated bit order. Five sources use ten binary variables.')
p('Let x_j be bit j, w_j be its block weight (1 or 2), c_j be its cost contribution, and d be demand in blocks. For example, 80 kWh means d = 8. The score is:')
h('Score = total operating cost + demand-mismatch penalty')
p('<b>E(x) = sum(c_j x_j) + P [sum(w_j x_j) - d]^2</b>')
p('The symbol sum means add all listed contributions. P is the penalty strength. Squaring the mismatch makes shortage and oversupply both costly.')
h('How the rules are enforced')
b('Capacity: a source cannot exceed three blocks because its two bits cannot represent more than three.')
b('Demand: exact equality is rewarded; every nonzero mismatch receives a penalty. The model does not allow free oversupply.')
b('Penalty choice: P equals the sum of all bit-cost contributions plus 1, which is 526 here. Costs are nonnegative and mismatch is an integer. Therefore any infeasible score is at least 526, while every feasible dispatch costs at most 525.')
p('This proves that an exact minimum of this score is feasible whenever a feasible allocation exists. It does not guarantee that an approximate quantum algorithm will measure that minimum.')

page(7,'How the quantum part works','QAOA and hybrid optimization')
p('A qubit is the basic unit of a quantum circuit. A quantum circuit is a sequence of mathematical operations on qubits followed by measurement, which produces ordinary bits. A statevector is the list of complex amplitudes used to simulate that quantum state on a normal computer.')
p('The Quantum Approximate Optimization Algorithm, abbreviated QAOA, is a method that alternates two types of circuit operations. A cost operation changes phases according to the score. A mixer operation changes how amplitudes are distributed among candidate states. Interference can make some outcomes more likely than others. [2]')
p('QAOA does not read every answer at once or guarantee the best answer. Measurement returns one bitstring: a string of zeros and ones describing one allocation. Repeated measurements produce a distribution of possible allocations.')
h('Hybrid quantum-classical optimization')
p('Hybrid means two kinds of computation work together. A classical optimizer changes circuit angles; a quantum circuit or its simulation evaluates their effect. In our implementation, a NumPy statevector routine evaluates the training score and the equivalent Qiskit circuit is verified and sampled afterward.')
b('NumPy is a Python library for numerical arrays. Python is the programming language used by this project.')
b('Qiskit is an open-source toolkit for constructing and running quantum circuits. We use its local StatevectorSampler to obtain simulated measurements.')
b('Constrained Optimization BY Linear Approximation, abbreviated COBYLA, is the classical angle-adjustment method, supplied by the SciPy scientific-computing library.')
p('The current setup uses three cost/mixer layers, six adjustable angles, three starting guesses and up to 180 score evaluations per guess. A shot is one measurement; the final circuit produces 4,096 shots. The fixed random seed, 42, makes the experiment reproducible in the tested environment.')

page(8,'The pipeline, start to finish','How we do it')
h('Small-scale quantum simulation')
p('This means a normal computer numerically imitates a small quantum circuit. Our example uses ten simulated qubits and 1,024 possible bitstrings. It is not an experiment on a physical quantum processor. No IBM account, application programming interface key or internet connection is needed after installation. An application programming interface is a software connection between systems; its key is a credential.')
b('<b>Read:</b> load demand, source capacities and costs from the input file.')
b('<b>Formulate:</b> build the QUBO score and list the encoded states for validation.')
b('<b>Benchmark:</b> find the exact classical answer and an economic merit-order answer. Merit order means filling demand from cheaper sources before more expensive ones.')
b('<b>Train:</b> adjust QAOA angles to reduce average penalized score. The average score includes demand penalties; it is different from a single feasible allocation\'s bill.')
b('<b>Verify:</b> compare the Qiskit circuit state with the independent NumPy simulation, allowing an irrelevant global phase. A global phase is a common amplitude rotation that does not affect measurement probabilities.')
b('<b>Measure:</b> take 4,096 Qiskit simulated shots. Keep the raw counts.')
b('<b>Decode:</b> evaluate the measured allocations, retain feasible ones and report the cheapest measured valid allocation. Also report the most frequent measured allocation, even if it violates demand.')
b('<b>Explain:</b> display source bars, cost comparison and demand coverage in the terminal.')
p('The exact answer is used for comparison, not inserted into the quantum samples. Selecting a good measured sample is classical post-processing: ordinary computation after measurement.')
p('Four tests check score construction across all states, independent circuit mathematics, invalid or impossible demand, and reproducible sampling. The Qiskit path also checks circuit equivalence before sampling.')

page(9,'What the demonstration proves','Measured allocations')
table(['Scenario','Exact cost','Best valid Qiskit sample','Feasible?'],[('80 kWh daytime','INR 110','INR 110','Yes'),('120 kWh surge','INR 300','INR 300','Yes'),('160 kWh demand','No feasible allocation','Simulation skipped','No')],[135,105,151,100])
h('80 kWh: every contribution explained')
p('Solar supplies 30 kWh for INR 24. Wind supplies 30 kWh for INR 36. Battery supplies 20 kWh for INR 50. Supply is 30 + 30 + 20 = 80 kWh. Cost is 24 + 36 + 50 = INR 110. Grid imports and diesel are unnecessary.')
h('120 kWh: handle the surge')
p('Solar, wind, battery and grid imports each supply 30 kWh. Their costs are INR 24, 36, 75 and 165. Supply is 120 kWh and total cost is INR 300. Diesel is unnecessary.')
h('160 kWh: recognize physical shortage')
p('The five sources can provide at most 150 kWh, leaving a 10 kWh shortage. An optimizer cannot create missing energy. The program records infeasibility and does not fabricate a quantum allocation.')
h('A fair interpretation')
p('An optimality gap is the difference between a reported cost and the exact minimum cost. The best feasible measured samples have a zero cost gap in the recorded examples. That is not proof of speedup: 4,096 shots explore a problem with only 1,024 states, and classical merit order is already exact for this simple model.')
p('The original training runs exhausted their angle-evaluation budgets without reporting convergence. The most frequent measured state can violate demand. Best valid sample, most frequent sample, feasible-shot share and optimizer status must be kept distinct. The raw Qiskit results are stored in results/qiskit_local.json.')

page(10,'Why quantum? Why keep classical?','Comparison and honesty')
p('A classical solver is an algorithm run on a conventional computer. Exhaustive search evaluates every encoded possibility. An exact solver certifies an optimum for its model when it finishes successfully. An approximate solver seeks a good answer without that guarantee.')
table(['Approach','What it contributes','Main limit here'],[('Exhaustive enumeration','Exact reference for the small encoded model.','Number of bitstrings doubles for every added bit.'),('Classical merit order','Fast, exact dispatch for our independent linear-cost resources.','Does not solve all future scheduling and coupled constraints.'),('Classical mathematical optimization','A strong future baseline for time-dependent energy and task scheduling.','Requires correct modeling; difficult integer cases may take longer.'),('Simulated QAOA','A testable quantum-circuit formulation and measurement workflow.','Approximate, training overhead and exponential simulation memory.')],[130,185,176])
p('We use quantum methods to investigate discrete scheduling choices and learn whether a hybrid approach can help on harder instances. We cannot currently justify replacing the classical solver on performance. Larger qubit counts alone do not establish an advantage.')
h('What would justify a stronger claim?')
b('Use identical inputs, constraints and objective for all methods. Compare feasible cost and unmet essential demand, not just penalized scores.')
b('Repeat random seeds and report successes and failures, total runtime, memory and preprocessing. Include strong classical baselines.')
b('Benchmark realistic instances before claiming that the quantum method is faster, cheaper, more reliable or better at scale.')
p('Our intended product distinction is understandable emergency decisions and verified recovery suggestions. We have not demonstrated that these capabilities outperform existing quantum or classical products.')

page(11,'Who benefits, and where?','Use cases and society')
p('The intended users are facility managers, campus energy teams, community organizations, students and researchers. A deployment-grade version would also need electrical engineers and qualified operators. The current prototype is designed for explanation and experiments.')
h('Small sites - proposed applications')
b('<b>Community shelter:</b> preserve lighting, water access and communications during a specified simulated outage.')
b('<b>Clinic:</b> explore refrigeration and communications priorities while rescheduling flexible activities. Actual clinical power planning requires qualified engineering and clinical review.')
b('<b>School or apartment:</b> compare battery reserves with electricity cost and delay discretionary charging.')
h('Large sites - proposed applications')
b('<b>Campus:</b> coordinate many buildings and flexible tasks under shared generation limits.')
b('<b>Industrial site:</b> schedule permitted nonurgent processes while maintaining essential operations.')
b('<b>Data center:</b> explore shifting authorized delay-tolerant computing jobs while respecting service deadlines and backup needs.')
p('Large-scale versions need more detailed classical models. A hybrid research design could let the classical layer handle site-wide balances and test QAOA on selected small scheduling decisions. This decomposition means splitting one large problem into smaller pieces; it can lose global optimality unless carefully coordinated and validated.')
h('Possible community benefit')
p('Explainable choices could help communities understand the tradeoff between expense and backup protection, identify shortages before an emergency and prioritize limited investment. Fairness matters: critical-load labels and priorities should be agreed with affected people, not silently chosen by the algorithm. These are expected benefits to test, not measured social outcomes.')

page(12,'Where REopt fits','Existing tools')
p('REopt is the name of an established energy-planning platform. Its official site is now hosted by the National Laboratory of the Rockies, abbreviated NLR; older materials use National Renewable Energy Laboratory, abbreviated NREL. [1]')
p('Its official overview describes planning of generation, storage and controllable loads, using a mixed-integer linear program. That is an optimization model combining continuous amounts and discrete choices with linear relationships. The public web tool supports economic and outage-resilience analysis. [1]')
h('How Q-Site should position itself')
b('REopt is a real-world reference for the importance of energy cost, storage dispatch and critical-load survival. Those ideas are not new inventions of Q-Site.')
b('Q-Site is currently a much smaller educational and research prototype. Its terminal makes a short modeled decision visible; its quantum circuit can be compared against an exact answer.')
b('The planned interactive failure tests and verified recovery explanations could provide a focused demonstration experience. Their usefulness must be tested with users.')
b('No REopt connection, validation study or head-to-head performance comparison has been implemented. We should not call Q-Site more accurate or capable than REopt.')
h('What makes the idea worth building?')
p('A compelling demonstration lets someone change an input, see a real shortage, and understand what action restores service. The value lies in helping people understand a decision and its tradeoffs, while exposing the actual role and limitations of the quantum algorithm.')
p('A scientific comparison must use matched problems. It would be misleading to compare a one-hour toy QUBO with a detailed multi-year planning study and attribute the difference to quantum computing.')

page(13,'Build cost, time and scale','Practical feasibility')
p('Development cost means the expense of building software. Operating cost in our energy model means the expense of electricity supply. They are separate budgets.')
b('<b>Current software:</b> no paid cloud service, hardware quantum account or commercial solver is required. On an existing computer, incremental license/service spending can be INR 0; developer time, electricity, internet and hardware ownership still have costs.')
b('<b>Physical deployment:</b> this prototype does not buy or install solar, batteries, generators, meters or control equipment. Those require separate site-specific quotations. We have no validated installation-cost estimate.')
b('<b>Planning estimate, not a quote:</b> a focused student-team extension may need 2-4 person-days for inputs and time-dependent battery logic, 2-4 for priorities/outage/recovery features, and 2-4 for testing and presentation. A person-day is one person working for one day. Integration problems may increase this 6-12 person-day estimate.')
h('Computing resources')
p('For n simulated qubits, one statevector has 2^n complex entries. At 16 bytes per entry, 10 qubits need about 16 KiB, 20 need 16 MiB, 30 need 16 GiB and 40 need 16 TiB. KiB, MiB, GiB and TiB are binary memory units; each is 1,024 times the previous unit. Program overhead requires additional memory.')
p('One QAOA evaluation uses repeated phase and mixer operations, with work roughly proportional to layers times qubits times 2^n in the present implementation. Training multiplies that by hundreds of evaluations. Our model also enumerates all states, so construction grows exponentially. These are classical simulation costs, not a forecast of physical quantum speed.')
p('The dashboard measures classical merit-order runs at 5, 50, 500 and 5,000 sources using seven repeats. It does not run quantum simulation at those larger sizes. Merit-order sorting grows roughly as N log N for N independent sources. Exact enumeration grows as 2^n. Multi-hour coupled problems require different baselines and measured benchmarks.')

page(14,'Run it, explain it, verify it','Demonstration and sources')
h('Run the current demonstration')
p('Open a terminal in the project folder. A terminal is the text window where commands are entered. Install dependencies once, then run:')
p('<font name="Courier">python -m pip install -r requirements-qiskit.txt<br/>python dashboard.py</font>')
p('Use <font name="Courier">python dashboard.py --cached</font> to display saved results without rerunning. Use <font name="Courier">--scenario 0</font> for daytime, <font name="Courier">--scenario 1</font> for the surge, <font name="Courier">--details</font> for technical evidence, or <font name="Courier">--scale</font> for the classical scaling laboratory.')
h('Challenge demonstration checklist')
b('<b>Formulation:</b> explain two bits per source and cost plus mismatch penalty (page 6).')
b('<b>Capacity and demand:</b> show encoded capacity and exact energy balance; demonstrate the 160 kWh shortage.')
b('<b>Allocation:</b> show source bars and add their contributions.')
b('<b>Cost and feasibility:</b> show INR 110 / INR 300 and confirm supplied energy equals demand.')
b('<b>Classical comparison:</b> show exact and merit-order costs, shot quality and measured solver times. State that this small example has no demonstrated quantum speedup.')
h('Evidence and next milestone')
p('Current evidence: results/qiskit_local.json, results/dashboard.txt, test_dispatch.py, and the circuit-equivalence check in qiskit_local.py. Reproduce with <font name="Courier">python -m unittest -v</font>. Next milestone: implement the proposed multi-hour outage model, validate it against an exact classical optimizer, then demonstrate user-triggered failures and verified recovery actions.')
h('Sources and provenance')
p('[1] National Laboratory of the Rockies, About REopt. Accessed 1 November 2026.<br/><link href="https://www.nlr.gov/reopt/about/index" color="#087f8c">https://www.nlr.gov/reopt/about/index</link>')
p('[2] Farhi, Goldstone and Gutmann (2014), A Quantum Approximate Optimization Algorithm.<br/><link href="https://arxiv.org/abs/1411.4028" color="#087f8c">https://arxiv.org/abs/1411.4028</link>')
p('Numerical results come from this project\'s synthetic inputs and saved local runs. Future resilience examples and implementation estimates are explicitly illustrative. The supplied reference PDF informed the simple question-and-explanation format; this document describes the current Q-Site direction and evidence afresh.')

page(15,'The Phase 1 idea','Judging criteria')
p('<b>Q-Site: an explainable energy reserve and recovery planner.</b> A community facility manager compares the cheapest energy allocation with an emergency-ready allocation, tests a specified grid outage, and sees the smallest tested intervention that restores essential service.')
p('The hackathon core is deliberately limited to one normal hour followed by one specified outage hour. The battery carries its remaining usable energy from the first hour into the second. Continuous multi-day scheduling and flexible-task deadlines remain stretch goals, not core delivery promises.')
table(['Criterion','Weight','What the submission will show'],[
('Problem understanding and Sustainable Development Goal relevance','20%','A facility manager, an explicit outage problem, affordability and service-continuity measures; page 16.'),
('Innovation and creativity','25%','Compare two plans, break both with the same outage, and verify a minimum tested recovery action; pages 16-17.'),
('Feasibility within the hackathon','20%','Reuse the working simulator infrastructure; deliver a tightly bounded offline model, with checkpoints and a fallback; page 17.'),
('Quantum component planning','25%','Explicit QUBO, local QAOA, small qubit budget, equivalent classical problem and repeated-run evaluation; page 18.'),
('Clarity of presentation','Not stated','Plain definitions, one user journey, aligned graphs and a short pitch; page 19. The remaining 10% is inferred, not confirmed.')],[132,54,305])
p('A Sustainable Development Goal, abbreviated SDG, is one of the United Nations goals for social, environmental and economic progress. The links below identify relevant goals; the prototype does not claim official endorsement or national impact.')
p('Status: the dispatch simulator already works. The reserve/outage/recovery workflow is the scoped implementation proposal for Phase 1. Revising the proposal does not turn planned features into completed software.')

page(16,'A concrete problem with social value','Problem, SDGs and innovation')
p('<b>Primary user:</b> a manager of a small community facility used as a shelter. <b>Decision:</b> how much battery energy should be used now versus preserved for a stated outage? <b>Consequence:</b> a cheap current plan may leave insufficient energy for essential services later.')
p('The demonstration uses a fictional Kochi shelter, not a claim about a particular real facility. Essential demand, outage duration and available resources are entered or selected by the user. Critical-load priorities are user choices, not decisions about whose needs matter made by the algorithm.')
table(['SDG link','How Q-Site relates','Project measure'],[
('7: Affordable and Clean Energy; target 7.1','Compare the expense of current supply with preservation of essential energy service.','Current-hour INR cost; essential kWh served during the specified outage.'),
('7: target 7.2','Include available solar and wind when allocating energy. This does not establish an increase in renewable adoption.','Direct solar-plus-wind kWh divided by total served kWh. Battery energy is not automatically counted as renewable.'),
('9: Industry, Innovation and Infrastructure; target 9.1','Explore the reliability of local energy provision under a specified failure.','Essential-energy shortfall in kWh; reserve remaining; tested recovery increment.')],[137,207,147])
p('These are local experiment measures, not the United Nations official SDG indicators. No carbon reduction is claimed without an emissions model. Sources: United Nations Goal 7 [3] and Goal 9 [4].')
h('The creative combination')
b('Show the price of protecting essential service, rather than only the cheapest bill.')
b('Let a judge change the outage conditions and see both plans re-evaluated.')
b('Replace a bare failure message with a verified recovery option: for example, the minimum extra usable battery energy among tested 10 kWh increments.')
p('Reserve planning already exists in tools such as REopt. The proposed distinction is this focused, explainable interaction with a visible quantum/classical experiment, not a claim to have invented resilience optimization.')

page(17,'A build we can finish','Feasibility and scope')
p('A minimum viable prototype is the smallest version that completes the user journey. Our core will use five sources, one normal hour, one outage hour, no charging between them, and battery energy measured at the usable output. Battery discharge power must also limit each hour; energy is not reset between the two hours.')
h('Assumed 24-hour remaining build window')
p('The actual hackathon duration was not supplied. This is a proposed time box for team work, not a commitment based on a confirmed schedule. The broader 6-12 person-day estimate on page 13 applies to the full multi-hour roadmap.')
table(['Time','Deliverable','Acceptance checkpoint'],[
('Hours 0-3','Validated inputs and fixed two-hour scenario.','Reject negative quantities and impossible reserve settings; show units.'),
('Hours 3-8','Classical allocation, reserve rule and outage evaluation.','Energy balance, capacity, battery carry-over and shortfall tests pass.'),
('Hours 8-13','Connect reserve-constrained dispatch to the quantum experiment.','Qiskit circuit verification passes; exact comparison uses identical inputs.'),
('Hours 13-17','Search extra usable battery energy in 10 kWh steps.','Each recommendation is re-solved; all smaller tested increments fail.'),
('Hours 17-21','Input prompts, charts, repeated-seed evidence.','Normal and shortage cases display correctly; raw measurements saved.'),
('Hours 21-24','Freeze scope, rehearse and package.','One fresh run and one clearly marked cached replay work offline.')],[65,208,218])
h('Fallback and delivery boundary')
p('If the deadline is shorter, use fixed outage presets and manual reserve input. Keep classical outage evaluation and mark quantum results as approximate; do not hide infeasible samples. Drop interactive editing, then recovery search, before compromising model correctness. Multi-day forecasts, physical controls, network physics and hardware quantum execution are outside the core.')
p('Software service budget: no paid service required on an existing machine. Use the installed Python, NumPy, SciPy, Qiskit and Rich libraries. Rich formats the terminal. Human effort and computer electricity are not free. No external network call is required for the demo after installation.')

page(18,'An explicit quantum experiment','25% quantum planning')
p('A reserve is battery energy deliberately kept unused. Let B be starting usable battery energy and R the chosen reserve. First-hour battery discharge must not exceed B minus R or the battery power limit times one hour. Remaining energy then feeds the outage evaluator. Other source availability and essential demand are specified separately for the outage hour.')
h('What the quantum subproblem solves')
p('For a fixed reserve R, minimize first-hour operating cost while meeting first-hour demand and source bounds. Use the cost-plus-demand-penalty QUBO on page 6. Reserve is a bound, not a hidden preference in the score. Classical code tests reserves, evaluates outage service and searches recovery increments; QAOA handles the explicitly identified dispatch subproblem.')
p('Use 10 kWh blocks and at most ten qubits. If a capacity changes, rebuild its bounded binary encoding: a one-block limit uses weight [1]; a two-block limit can use [1,1]; a three-block limit uses [1,2]. Zero capacity needs no variable. Reject values that cannot be represented at the stated resolution. Recalculate the penalty for each model. Test all encoded states to verify bounds and score equality.')
h('Circuit and experiment budget')
b('Use local Qiskit simulation. Start with one or two QAOA layers and at most ten qubits; keep the existing three-layer case as a comparison if runtime permits.')
b('Use the existing classical angle-training routine and verify the equivalent Qiskit circuit before sampling. Initial budget: two starts, 100 evaluations per start and 2,048 shots; record any later changes.')
b('Run five declared random seeds on the same scenarios. Preserve raw counts, optimizer status, total runtime, feasible-shot share, exact-optimum probability and best feasible sample gap.')
b('Compare exact enumeration and classical merit order on identical encoded inputs. With duplicate encodings, sum probabilities over every optimal allocation, not one bitstring.')
p('Acceptance is correct modeling and transparent measurement, not guaranteed quantum victory. If no feasible sample is measured, report it. State which layer ran classically. The reason for exploring quantum is a controlled test of binary allocation methods; this simple linear model currently favors classical methods on practicality.')

page(19,'Make the idea easy to judge','Presentation and evidence')
h('The 90-second story')
b('<b>0-15 seconds - problem:</b> a shelter needs affordable electricity now and essential electricity during an outage. Spending all battery energy early can undermine the latter.')
b('<b>15-35 seconds - idea:</b> show Lowest Cost and Emergency Ready. Define reserve as energy saved for later. Display the extra current-hour cost of that reserve.')
b('<b>35-55 seconds - interaction:</b> trigger the same outage for both plans. Show essential demand, energy served, shortfall and battery remaining in consistent units.')
b('<b>55-75 seconds - recovery:</b> when service is insufficient, show the smallest successful extra-battery increment among the tested choices, with its assumptions. If none works, say so.')
b('<b>75-90 seconds - quantum and evidence:</b> identify the QUBO allocation decision, the Qiskit simulation and the exact classical comparison. Report whether measured outcomes are feasible. State that speedup is not established.')
h('What must be visible on screen')
p('Keep one question per view: What are the inputs? What does each source supply? What does protection cost? What happens during the outage? What tested change fixes it? Use aligned graphs, clear units and plain labels. Keep technical circuit counts and optimizer charts in the optional details view.')
h('Phase 1 submission package')
p('Submit the problem and SDG mapping, the fixed scope, the QUBO/circuit plan, the time-boxed task list, the risks/fallback, and existing simulator evidence. An implementation-status checklist must distinguish current allocation results from proposed resilience results. No slide should imply those extensions have already been tested.')
h('Success criteria for the proposed extension')
p('Every reported feasible allocation balances energy; capacity and battery limits hold; reserve carry-over is correct; both plans face the same outage; recovery is verified against all smaller tested increments; classical and quantum results use the same inputs; unsuccessful samples and runs remain visible. These are tests to implement, not tests claimed as passed today.')
p('[3] United Nations, Goal 7 targets:<br/><link href="https://www.un.org/sustainabledevelopment/energy/" color="#087f8c">https://www.un.org/sustainabledevelopment/energy/</link><br/>[4] United Nations, Goal 9, target 9.1:<br/><link href="https://sdgs.un.org/goals/goal9" color="#087f8c">https://sdgs.un.org/goals/goal9</link><br/>Sources accessed 1 November 2026. Clarity weight remains unconfirmed; 10% is inferred from the supplied weights summing to 90%.')

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#cbd9df')); canvas.line(52,43,543,43)
    canvas.setFont('Helvetica',9);canvas.setFillColor(colors.HexColor('#526978'))
    canvas.drawString(52,29,'Q-Site | Plain-language project explainer | 01 Nov 2026')
    canvas.drawRightString(543,29,str(doc.page));canvas.restoreState()

doc=SimpleDocTemplate(str(OUT/'Q-Site_Complete_Explainer.pdf'),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=40,bottomMargin=57,title='Q-Site - Complete Plain-Language Explainer',author='JeL')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT/'Q-Site_Complete_Explainer.pdf')

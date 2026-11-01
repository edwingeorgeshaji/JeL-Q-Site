import fs from 'node:fs/promises';
import {Presentation,PresentationFile} from 'file:///C:/Users/edwin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {makeNativeBulletParagraphs,finalizePresentation} from 'file:///C:/Users/edwin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root='C:/D/Code/Quantum Hack Day - Kochi';
const skill='C:/Users/edwin/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const purple='#30195B',pink='#F37EB5';
const p=Presentation.create({slideSize:{width:1280,height:720}});
function text(s,value,x,y,w,h,size=28,color=purple,bold=false){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=value;a.text.style={typeface:'Arial',fontSize:size,color,bold};return a;}
function base(title,subtitle){const s=p.slides.add();s.background.fill='#FFFFFF';text(s,'Q-SITE',64,32,500,30,18,pink,true);text(s,title,64,105,1150,100,48,purple,true);if(subtitle)text(s,subtitle,64,205,1130,65,25);text(s,String(p.slides.items.length).padStart(2,'0'),1160,665,65,30,18,pink,true);return s;}
function bullets(s,items,y=295,size=30){const a=text(s,'',64,y,1130,330,size);a.text=makeNativeBulletParagraphs(items,{marginLeftPoints:20,hangingPoints:10,spaceAfterPoints:18});return a;}
let s=base('','');
text(s,'Q-Site',64,195,850,150,112,purple,true);
text(s,'Energy planning with quantum optimization',70,370,1110,60,36);
text(s,'Affordable electricity. Backup for essential services.',70,445,1100,55,28);
text(s,'|0⟩  |1⟩',880,95,330,95,58,pink);
s.speakerNotes.text='Q-Site is a local Qiskit prototype. It plans one normal hour followed by one outage hour. The quantum notation shows the basic states of a qubit.';
s=base('The problem and our solution','A cheaper plan today can leave too little battery energy for a power cut.');
bullets(s,[
 'Inputs: normal demand, essential outage demand and stored battery energy.',
 'Allocate solar, wind, battery, grid electricity and diesel within their limits.',
 'Compare spending less now with saving battery energy for later.',
 'Show cost, outage coverage, shortages and extra battery energy needed.'
]);
text(s,'For shelters, clinics, homes and small businesses',64,632,1120,35,24,pink,true);
s.speakerNotes.text='Energy allocation means deciding how much each source supplies. Essential loads include lighting, refrigeration and communications. Grid electricity comes from the public network. The simple input mode asks three questions and uses fixed example source limits and rates. Advanced mode exposes more conditions. The battery carries remaining energy into the outage and does not recharge. Recovery tests extra starting battery energy in 10 kWh increments with the same power limits. It does not price equipment purchases.';
s=base('How the quantum component works','Hybrid means a classical computer and a quantum circuit work together.');
bullets(s,[
 'QUBO scores 0/1 energy choices using cost and a penalty for unmet demand.',
 'QAOA tunes a quantum circuit to favour choices with lower scores.',
 'Qiskit simulates the circuit locally and measures candidate allocations.',
 'Check measured solutions against demand, capacity and the exact classical answer.'
],295,30);
text(s,'QUBO = Quadratic Unconstrained Binary Optimization',64,624,1150,30,21,pink,true);
text(s,'QAOA = Quantum Approximate Optimization Algorithm',64,655,1090,30,21,pink,true);
s.speakerNotes.text='QUBO represents source quantities using binary variables. Demand mismatch receives a squared penalty and bounded encodings enforce source capacity. Reserve planning reduces available battery discharge before the outage. QAOA uses alternating cost and mixer operations. Classical COBYLA optimization adjusts its angles using Qiskit Statevector evaluations. StatevectorSampler draws 2,048 final measurements per trial. The prototype selects the best feasible measured sample. An independent NumPy statevector check validates circuit equivalence. QAOA reference: https://arxiv.org/abs/1411.4028 . There is no guarantee that QAOA finds the optimum on every run.';
s=base('Results, impact and future scope','Example: 70 kWh before the outage, 20 kWh essential demand, 10 kWh in the battery.');
bullets(s,[
 'Spend less: INR 85 now, then supply 0 of 20 kWh during the outage.',
 'Save battery: INR 115 now, then supply 10 of 20 kWh during the outage.',
 'Six simulation runs matched the classical minimum cost. No speed advantage established.',
 'Next: full-day planning, forecasts, battery charging and community microgrids.'
],300,29);
text(s,'Goal: affordable energy and stronger outage protection',64,638,1130,35,24,pink,true);
s.speakerNotes.text='Evidence: user terminal screenshots from the implemented prototype with demand 70 kWh, critical demand 20 kWh and starting battery 10 kWh. Outage solar, wind and diesel availability are all zero. Cheapest normal allocation is solar 30, wind 30, battery 10 kWh for INR 24+36+25=85. Reserve plan uses grid 10 instead of battery for INR 24+36+55=115. These are illustrative normal-hour operating costs, excluding equipment and installation. Reserving battery costs INR 30 extra and still leaves a 10 kWh outage shortfall. Starting with 20 kWh extra battery energy fixes the cheapest plan in this example. Each of six runs found a valid measured allocation at the exact classical minimum, which does not imply every shot succeeded. Present simulation is small scale. Future work includes losses, degradation, real meter data, strong classical benchmarks and quantum hardware tests. Large-scale quantum benefit remains unproven. REopt provides an established classical planning reference for energy cost and resilience: https://www.nlr.gov/reopt/about/index . Q-Site has no REopt integration or superiority benchmark. Community applications support the goals of affordable, reliable energy and resilient infrastructure.';
s=base('','');
text(s,'Thank you',64,220,1100,120,88,purple,true);
text(s,'Q-Site',68,355,1000,75,48,pink,true);
text(s,'Questions and demonstration',68,460,1100,60,32);
text(s,'|0⟩ + |1⟩',860,100,350,90,50,pink);
s.speakerNotes.text='Run python dashboard.py for the interactive demonstration. Explain the input scenario and compare the two strategies before discussing the quantum validation.';
await fs.mkdir(root+'/.deck-build/short-render',{recursive:true});
for(let i=0;i<p.slides.items.length;i++){const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(root+`/.deck-build/short-render/slide-${i+1}.png`,new Uint8Array(await blob.arrayBuffer()));}
const candidate=root+'/.deck-build/short-candidate.pptx';await(await PresentationFile.exportPptx(p)).save(candidate);
console.log(await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:root+'/output/slides/Q-Site_Overview_5_Slides.pptx',pythonExecutable:'C:/Users/edwin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:5,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:root+'/.deck-build/short-validation.json'}));

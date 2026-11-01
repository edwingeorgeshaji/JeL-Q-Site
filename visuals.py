"""Standalone SVG result figures; no browser or plotting dependency needed."""
from html import escape


def render(report, output):
    colors = ['#e6aa24', '#238c82', '#6574c4', '#39759d', '#bc5d52']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="780" viewBox="0 0 1120 780" role="img" aria-label="JeL energy dispatch results">',
             '<rect width="1120" height="780" fill="#f6f5ef"/>',
             '<style>text{font-family:Arial,sans-serif;fill:#192c35} .small{font-size:14px} .label{font-size:18px}</style>',
             '<text x="50" y="55" font-size="30" font-weight="bold">JeL / Q-SITE</text>',
             '<text x="50" y="86" class="label">Energy dispatch · fresh local QAOA simulation</text>']
    sources = report['config']['sources']
    for i, source in enumerate(sources):
        x = 50+i*210
        parts += [f'<rect x="{x}" y="115" width="13" height="13" fill="{colors[i%len(colors)]}"/>',
                  f'<text x="{x+21}" y="127" class="small">{escape(source["name"])}</text>']
    for k, r in enumerate(report['scenarios']):
        y = 180+k*175
        parts.append(f'<text x="50" y="{y}" class="label" font-weight="bold">{escape(r["name"])} / Demand {r["demand_kwh"]} kWh</text>')
        if r['exact'] is None:
            parts.append(f'<text x="50" y="{y+40}" class="label">INFEASIBLE: capacity {r["capacity_kwh"]} kWh; no allocation can meet demand.</text>')
            continue
        for line, (label, allocation) in enumerate([('Exact', r['exact']), ('QAOA best sample', r.get('qaoa'))]):
            by = y+20+line*39
            parts.append(f'<text x="50" y="{by+20}" class="small">{label}</text>')
            x = 210
            if allocation is None:
                parts.append(f'<text x="210" y="{by+20}" class="small">No feasible measured sample</text>')
                continue
            for i, source in enumerate(sources):
                value = allocation['sources_kwh'][source['name']]
                width = value*4
                if width:
                    parts += [f'<rect x="{x}" y="{by}" width="{width}" height="28" fill="{colors[i%len(colors)]}"/>',
                              f'<text x="{x+5}" y="{by+19}" font-size="13" style="fill:white">{value}</text>']
                x += width
            parts.append(f'<text x="{x+15}" y="{by+20}" class="small">INR {allocation["cost_inr"]:.0f}</text>')
        parts.append(f'<text x="50" y="{y+125}" class="small">Optimal-state probability {r["optimal_probability"]:.2%} · uniform {r["uniform_optimal_probability"]:.2%} · feasible shots {r["feasible_shots"]}/{report["settings"]["shots"]}</text>')
    parts += ['<text x="50" y="728" class="small">Synthetic one-hour scenarios. Battery starts charged. Bar labels: kWh. No quantum speedup claim.</text>',
              '<text x="50" y="754" class="small">QAOA result uses lowest-cost feasible measured sample; the modal sample is separately reported in JSON.</text>', '</svg>']
    (output/'dispatch.svg').write_text('\n'.join(parts), encoding='utf-8')
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="490" viewBox="0 0 1000 490">',
             '<rect width="1000" height="490" fill="white"/>',
             '<g font-family="Arial" fill="#192c35"><text x="60" y="35" font-size="23">QAOA optimizer evaluations / expected QUBO energy</text>']
    for k,r in enumerate(report['scenarios']):
        history = r.get('history')
        if not history:
            continue
        lo, hi = min(history), max(history)
        span = max(hi-lo, 1)
        points = ' '.join(f'{60+880*i/max(len(history)-1,1):.2f},{390-290*(v-lo)/span:.2f}' for i,v in enumerate(history))
        parts += [f'<polyline points="{points}" fill="none" stroke="{colors[k]}" stroke-width="1.4"/>',
                  f'<text x="60" y="{430+k*23}">{escape(r["name"])}: {lo:.1f} to {hi:.1f} INR penalized energy (each trace scaled separately)</text>']
    parts += ['<text x="60" y="75">Includes restart boundaries; lower is better. Expected energy includes demand penalties.</text></g></svg>']
    (output/'convergence.svg').write_text('\n'.join(parts), encoding='utf-8')

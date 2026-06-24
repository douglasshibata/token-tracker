import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  standalone: false,
  selector: 'app-coverage-analysis',
  template: `
    <div class="analysis-container">
      <h2>Coverage Gap Analysis</h2>

      <div class="coverage-metrics">
        <div class="metric-box">
          <label>Gateway (Opt-in)</label>
          <div class="val">{{ stats.gateway_pct }}%</div>
          <div class="progress"><div class="bar" [style.width.%]="stats.gateway_pct"></div></div>
        </div>
        <div class="metric-box">
          <label>Intercept (Passive)</label>
          <div class="val">{{ stats.intercept_pct }}%</div>
          <div class="progress"><div class="bar orange" [style.width.%]="stats.intercept_pct"></div></div>
        </div>
      </div>

      <div class="migration-alert" *ngIf="stats.intercept_count > 0">
        ⚠️ <strong>{{ stats.intercept_count }} requests</strong> bypassing gateway.
        Consider migration outreach to identified IP ranges.
      </div>

      <div class="unidentified-ips">
        <h3>Top Unidentified Sources</h3>
        <ul>
          <li *ngFor="let ip of stats.top_intercept_ips">{{ ip.source_ip }} ({{ ip.count }} calls)</li>
        </ul>
      </div>
    </div>
  `,
  styles: [`
    .analysis-container { padding: 20px; background: #fff; border: 1px solid #ddd; }
    .coverage-metrics { display: flex; gap: 20px; margin: 20px 0; }
    .metric-box { flex: 1; text-align: center; }
    .progress { height: 10px; background: #eee; border-radius: 5px; overflow: hidden; }
    .bar { height: 100%; background: green; }
    .bar.orange { background: orange; }
    .migration-alert { padding: 10px; background: #fff3cd; border: 1px solid #ffeeba; border-radius: 4px; }
  `]
})
export class CoverageAnalysisComponent implements OnInit {
  stats: any = { gateway_pct: 0, intercept_pct: 0, intercept_count: 0, top_intercept_ips: [] };

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    // In real app, call /v1/logs/coverage-stats
    this.stats = {
      gateway_pct: 72,
      intercept_pct: 28,
      intercept_count: 145,
      top_intercept_ips: [
        { source_ip: '10.0.1.45', count: 42 },
        { source_ip: '10.0.2.12', count: 18 }
      ]
    };
  }
}

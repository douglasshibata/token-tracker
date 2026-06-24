import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  standalone: false,
  selector: 'app-request-logs',
  template: `
    <div class="logs-container">
      <h2>Global Request Logs (Unified)</h2>
      <div class="filters">
        <select [(ngModel)]="sourceFilter" (change)="loadLogs()">
          <option value="">All Sources</option>
          <option value="gateway">Gateway (Proxy)</option>
          <option value="intercept">Intercept (MITM)</option>
        </select>
      </div>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>AI Tool</th>
            <th>Type</th>
            <th>Provider</th>
            <th>Model</th>
            <th>Tokens (I/O)</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let req of logs">
            <td>{{ req.created_at | date:'short' }}</td>
            <td><span class="source-badge" [attr.data-source]="req.source_type">{{ req.source_type || 'unknown' }}</span></td>
            <td><span [class]="req.capture_mode">{{ req.capture_mode }}</span></td>
            <td>{{ req.provider_name }}</td>
            <td>{{ req.model }}</td>
            <td>{{ req.input_tokens }} / {{ req.output_tokens }}</td>
            <td>\${{ req.cost | number:'1.2-6' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .gateway { color: green; font-weight: bold; }
    .intercept, .intercept-mitm { color: orange; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border-bottom: 1px solid #ddd; text-align: left; }
    .source-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; font-weight: 600; }
    .source-badge[data-source="kiro"] { background: #e8f5e9; color: #2e7d32; }
    .source-badge[data-source="kiro-agent"] { background: #e8f5e9; color: #2e7d32; }
    .source-badge[data-source="claude-cli"] { background: #e3f2fd; color: #1565c0; }
    .source-badge[data-source="antigravity"] { background: #f3e5f5; color: #7b1fa2; }
    .source-badge[data-source="cursor"] { background: #fff3e0; color: #e65100; }
    .source-badge[data-source="unknown"] { background: #f5f5f5; color: #757575; }
  `]
})
export class RequestLogsComponent implements OnInit {
  logs: any[] = [];
  sourceFilter = '';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs() {
    let url = '/v1/logs/00000000-0000-0000-0000-000000000000'; // Default user for demo
    if (this.sourceFilter) url += `?source=${this.sourceFilter}`;
    this.http.get<any[]>(url).subscribe(data => this.logs = data);
  }
}

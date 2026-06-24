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
            <td><span [class]="req.source_type">{{ req.source_type }}</span></td>
            <td>{{ req.provider_name }}</td>
            <td>{{ req.model }}</td>
            <td>{{ req.input_tokens }} / {{ req.output_tokens }}</td>
            <td>\${{ req.total_cost | number:'1.2-6' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .gateway { color: green; font-weight: bold; }
    .intercept { color: orange; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border-bottom: 1px solid #ddd; text-align: left; }
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

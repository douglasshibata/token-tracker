import { Component, OnInit } from '@angular/core';
import { LogsService } from '../../core/services/logs.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  stats: any = { total_spend: 0, total_tokens: 0, blocked_count: 0 };
  projectId = '00000000-0000-0000-0000-000000000000';

  constructor(private logsService: LogsService) {}

  ngOnInit(): void {
    this.loadStats();
    // Poll stats every 10 seconds
    setInterval(() => this.loadStats(), 10000);
  }

  loadStats() {
    this.logsService.getStats(this.projectId).subscribe(data => {
      this.stats = data;
    });
  }
}

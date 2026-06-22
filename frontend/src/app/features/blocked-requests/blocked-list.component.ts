import { Component, OnInit } from '@angular/core';
import { LogsService } from '../../core/services/logs.service';

@Component({
  selector: 'app-blocked-list',
  templateUrl: './blocked-list.component.html'
})
export class BlockedRequestsComponent implements OnInit {
  blockedLogs: any[] = [];
  projectId = '00000000-0000-0000-0000-000000000000';

  constructor(private logsService: LogsService) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs() {
    this.logsService.getLogs(this.projectId).subscribe(logs => {
      this.blockedLogs = logs.filter(l => l.was_blocked);
    });
  }
}

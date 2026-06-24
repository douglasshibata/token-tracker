import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  standalone: false,
  selector: 'app-monthly-report',
  templateUrl: './monthly-report.component.html',
  styleUrls: ['./monthly-report.component.css']
})
export class MonthlyReportComponent implements OnInit {
  selectedYear = new Date().getFullYear();
  selectedMonth = new Date().getMonth() + 1;
  projectId = '00000000-0000-0000-0000-000000000000';

  reportData: any;
  loading = false;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadReportData();
  }

  loadReportData() {
    this.loading = true;
    this.http.get(`/v1/logs/summary/${this.projectId}?year=${this.selectedYear}&month=${this.selectedMonth}`)
      .subscribe(data => {
        this.reportData = data;
        this.loading = false;
      });
  }

  downloadRawData(format: 'csv' | 'excel') {
    window.location.href = `/v1/export/monthly?project_id=${this.projectId}&year=${this.selectedYear}&month=${this.selectedMonth}&format=${format}`;
  }

  generatePDF() {
    window.print();
  }
}

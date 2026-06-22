import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-productivity',
  templateUrl: './productivity.component.html',
  styleUrls: ['./productivity.component.css']
})
export class ProductivityComponent implements OnInit {
  stats: any = { total_prompts: 0, generation_ratio: 0, cost_per_prompt: 0, code_vs_chat_percentage: 0 };
  topTools: any[] = [];
  projectId = '00000000-0000-0000-0000-000000000000';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadProductivity();
  }

  loadProductivity() {
    this.http.get(`/v1/logs/productivity/${this.projectId}`).subscribe((data: any) => {
      this.stats = data.stats || this.stats;
      this.topTools = data.top_tools || [];
    });
  }

  getEfficiencyLabel(ratio: number): string {
    if (ratio > 100) return "Highly Productive";
    if (ratio > 50) return "Balanced";
    return "Inefficient (Context Heavy)";
  }
}

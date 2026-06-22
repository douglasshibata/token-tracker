import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { BudgetService } from '../../core/services/budget.service';

@Component({
  selector: 'app-limit-form',
  templateUrl: './limit-form.component.html',
  styleUrls: ['./limit-form.component.css']
})
export class LimitFormComponent implements OnInit {
  limitForm!: FormGroup;
  projectId = '00000000-0000-0000-0000-000000000000';

  constructor(
    private fb: FormBuilder,
    private budgetService: BudgetService
  ) {}

  ngOnInit(): void {
    this.limitForm = this.fb.group({
      daily_limit: [null, [Validators.min(0)]],
      monthly_limit: [null, [Validators.min(0)]],
      total_limit: [null, [Validators.min(0)]]
    });
    this.loadCurrentLimits();
  }

  loadCurrentLimits() {
    this.budgetService.getLimits(this.projectId).subscribe(limits => {
      this.limitForm.patchValue(limits);
    });
  }

  enforceLimits() {
    if (this.limitForm.invalid) return;
    this.budgetService.updateLimits(this.projectId, this.limitForm.value).subscribe({
      next: () => alert('🛡️ Hard Limits Enforced!'),
      error: (err) => alert('Failed to update')
    });
  }
}

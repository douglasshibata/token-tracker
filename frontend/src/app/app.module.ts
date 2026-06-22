import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { ProductivityComponent } from './features/dashboard/productivity.component';
import { MonthlyReportComponent } from './features/dashboard/monthly-report.component';
import { LimitFormComponent } from './features/limits/limit-form.component';
import { BlockedRequestsComponent } from './features/blocked-requests/blocked-list.component';

const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'productivity', component: ProductivityComponent },
  { path: 'report', component: MonthlyReportComponent },
  { path: 'limits', component: LimitFormComponent },
  { path: 'blocked', component: BlockedRequestsComponent }
];

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    ProductivityComponent,
    MonthlyReportComponent,
    LimitFormComponent,
    BlockedRequestsComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    ReactiveFormsModule,
    FormsModule,
    RouterModule.forRoot(routes)
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }

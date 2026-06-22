import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: `
    <nav>
      <a routerLink="/dashboard">Dashboard</a> |
      <a routerLink="/productivity">Productivity</a> |
      <a routerLink="/report">Monthly Report</a> |
      <a routerLink="/limits">Hard Limits</a> |
      <a routerLink="/blocked">Blocked Requests</a>
    </nav>
    <hr>
    <router-outlet></router-outlet>
  `,
  styles: [`
    nav { padding: 1rem; background: #f4f4f4; }
    a { margin-right: 1rem; text-decoration: none; color: #333; font-weight: bold; }
    a:hover { color: #007bff; }
  `]
})
export class AppComponent {
  title = 'Token Tracker Dashboard';
}

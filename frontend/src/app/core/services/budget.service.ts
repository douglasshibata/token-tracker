import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class BudgetService {
  private apiUrl = '/v1/projects';

  constructor(private http: HttpClient) { }

  getLimits(projectId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/${projectId}`);
  }

  updateLimits(projectId: string, limits: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/${projectId}`, limits);
  }
}

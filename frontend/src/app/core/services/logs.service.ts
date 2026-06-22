import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LogsService {
  private apiUrl = '/v1/logs';

  constructor(private http: HttpClient) { }

  getLogs(projectId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/${projectId}`);
  }

  getStats(projectId: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/stats/${projectId}`);
  }
}

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { timeout } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class FormationService {

  private apiUrl = '/api';

  constructor(private http: HttpClient) {}

  // 🔹 Get all savoir-agir
  getSavoirAgir(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/savoir-agir`);
  }

  // 🔹 Get jalons by savoir-agir id
  getJalons(savoirId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/jalons/${savoirId}`);
  }

  // 🔹 Save AC to backend (optional if you want later)
  saveAC(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/ac`, data);
  }

  alignAAD(data: {
    aad_text: string;
    formation_id: string;
    threshold: number;
    limit: number;
  }): Observable<any> {
    return this.http.post(`${this.apiUrl}/align`, data).pipe(
      timeout(90000),
    );
  }

  identifyAADs(files: File[], subjectId: string): Observable<any> {
    const form = new FormData();
    files.forEach((file) => form.append('files', file));
    form.append('subject_id', subjectId);
    return this.http.post(`${this.apiUrl}/identify`, form).pipe(
      timeout(300000),
    );
  }

  getGeneratedAADs(subjectId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/aad/${encodeURIComponent(subjectId)}`);
  }

    // 🔥 NEW — Export full formation JSON
  exportFormation(formationId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/export/${formationId}`);
  }
  
}

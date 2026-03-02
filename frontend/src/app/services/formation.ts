import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class FormationService {

  private apiUrl = 'http://localhost:5000/api';

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

    // 🔥 NEW — Export full formation JSON
  exportFormation(formationId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/export/${formationId}`);
  }
  
}
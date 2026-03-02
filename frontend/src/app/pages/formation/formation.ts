import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

type FormationItem = {
  id: string;
  title: string;
  subtitle?: string;
};

@Component({
  selector: 'app-formation',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './formation.html',
  styleUrl: './formation.css',
})
export class Formation {
  formations: FormationItem[] = [
    { id: 'iti', title: 'ITI', subtitle: 'Ingénierie et Technologies de l’Information' },
    { id: 'stpi', title: 'STPI', subtitle: 'Sciences et Technologies pour l’Ingénieur' },
    { id: 'autre', title: 'Autre', subtitle: 'À compléter' },
  ];

  constructor(private router: Router) {}

  selectFormation(id: string) {
    // Étape suivante: /metier (avec formation en param dans l'URL)
    this.router.navigate(['/metier', id]);
  }
}

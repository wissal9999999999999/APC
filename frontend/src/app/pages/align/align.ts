import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

type ResultItem = { aad: string; score: number };

@Component({
  selector: 'app-align',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './align.html',
  styleUrl: './align.css',
})
export class Align {
  ac = '';
  loading = false;
  error = '';
  results: ResultItem[] = [];

  private demoDB: ResultItem[] = [
    { aad: 'Implémenter une liste chaînée en C', score: 0.92 },
    { aad: 'Écrire une fonction de tri (insertion, fusion)', score: 0.88 },
    { aad: 'Manipuler des pointeurs et la mémoire dynamique', score: 0.84 },
    { aad: 'Analyser la complexité temporelle d’un algorithme', score: 0.79 },
    { aad: 'Utiliser des structures (struct) et des tableaux', score: 0.74 },
  ];

  search(): void {
    this.error = '';
    const q = this.ac.trim();

    if (!q) {
      this.results = [];
      this.error = 'Veuillez saisir un AC.';
      return;
    }

    this.loading = true;

    setTimeout(() => {
      this.results = this.demoDB;
      this.loading = false;
    }, 400);
  }
}

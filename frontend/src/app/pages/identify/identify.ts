import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

type AADItem = { text: string };

@Component({
  selector: 'app-identify',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './identify.html',
  styleUrl: './identify.css',
})
export class Identify {
  subjectId = '';

  file: File | null = null;
  loading = false;
  error = '';
  aads: AADItem[] = [];

  constructor(private route: ActivatedRoute, private router: Router) {
    this.subjectId = this.route.snapshot.paramMap.get('id') ?? '';
  }

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.error = '';
    this.aads = [];

    if (!input.files || input.files.length === 0) {
      this.file = null;
      return;
    }

    this.file = input.files[0];
  }

  async identify() {
    this.error = '';
    this.aads = [];

    if (!this.file) {
      this.error = 'Veuillez sélectionner un fichier (PDF).';
      return;
    }

    this.loading = true;

    try {
      // ✅ VERSION DEMO (pour tester l’UI tout de suite)
      // ensuite on remplacera par un vrai appel backend (FastAPI)
      await new Promise((r) => setTimeout(r, 900));

      this.aads = [
        { text: "Comprendre la notion de langage formel" },
        { text: "Reconnaître un automate fini déterministe" },
        { text: "Écrire des expressions régulières simples" },
        { text: "Analyser un langage accepté par un automate" },
      ];

      // ✅ Quand tu brancheras le backend, on fera:
      // const form = new FormData();
      // form.append('file', this.file);
      // form.append('subject', this.subjectId);
      // const res = await fetch('http://127.0.0.1:8000/identify', { method: 'POST', body: form });
      // const data = await res.json();
      // this.aads = data.aads.map((x: string) => ({ text: x }));

    } catch (e) {
      this.error = "Erreur pendant l'identification.";
    } finally {
      this.loading = false;
    }
  }

  back() {
    this.router.navigate(['/subject', this.subjectId]);
  }
}

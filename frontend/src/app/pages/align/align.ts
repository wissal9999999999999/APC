import { ChangeDetectorRef, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs/operators';
import { FormationService } from '../../services/formation';

type ResultItem = { rank: number; ac_id: string; ac_title: string; score: number };
type BatchAlignment = {
  aad_id: string;
  aad_text: string;
  top_match: ResultItem | null;
  matches: ResultItem[];
};

@Component({
  selector: 'app-align',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './align.html',
  styleUrl: './align.css',
})
export class Align {
  aad = '';
  threshold = 0.3;
  loading = false;
  error = '';
  topMatch: ResultItem | null = null;
  results: ResultItem[] = [];
  jsonFile: File | null = null;
  batchLoading = false;
  batchError = '';
  batchResults: BatchAlignment[] = [];
  batchDownloadReady = false;
  subjectId = '';
  private formationId = 'iti';

  constructor(
    private route: ActivatedRoute,
    private formationService: FormationService,
    private changeDetector: ChangeDetectorRef,
  ) {
    this.subjectId = this.route.snapshot.paramMap.get('id') ?? 'matiere';
  }

  search(): void {
    this.error = '';
    const q = this.aad.trim();

    if (!q) {
      this.topMatch = null;
      this.results = [];
      this.error = 'Veuillez saisir un AAD.';
      return;
    }

    this.loading = true;

    this.formationService.alignAAD({
      aad_text: q,
      formation_id: this.formationId,
      threshold: this.threshold,
      limit: 10,
    }).pipe(
      finalize(() => {
        this.loading = false;
      }),
    ).subscribe({
      next: (response) => {
        this.results = response.matches ?? [];
        this.topMatch = response.top_match ?? this.results[0] ?? null;
      },
      error: (err) => {
        console.error(err);
        this.topMatch = null;
        this.results = [];
        this.error = err.name === 'TimeoutError'
          ? "Le moteur d'alignement a dépassé 90 secondes. Veuillez réessayer."
          : err.error?.error ?? "Impossible d'effectuer l'alignement.";
      },
    });
  }

  onJsonChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.jsonFile = input.files?.[0] ?? null;
    this.batchResults = [];
    this.batchError = '';
    this.batchDownloadReady = false;
  }

  async alignJson(): Promise<void> {
    this.batchError = '';
    this.batchResults = [];
    this.batchDownloadReady = false;
    if (!this.jsonFile) {
      this.batchError = 'Veuillez sélectionner un fichier JSON contenant des AAD.';
      return;
    }

    this.batchLoading = true;
    try {
      const form = new FormData();
      form.append('file', this.jsonFile);
      form.append('subject_id', this.subjectId);
      form.append('formation_id', this.formationId);
      form.append('threshold', String(this.threshold));
      form.append('limit', '3');

      const response = await fetch('/api/align/json', { method: 'POST', body: form });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error ?? `Erreur HTTP ${response.status}`);
      }
      this.batchResults = data.alignments ?? [];
      this.batchDownloadReady = true;
    } catch (error) {
      console.error(error);
      this.batchError = error instanceof Error
        ? error.message
        : "Impossible d'aligner le fichier JSON.";
    } finally {
      this.batchLoading = false;
      this.changeDetector.detectChanges();
    }
  }

  downloadBatchAlignment(): void {
    window.location.href = `/api/align/${encodeURIComponent(this.subjectId)}/download`;
  }
}

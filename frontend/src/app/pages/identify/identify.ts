import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormationService } from '../../services/formation';

type AADItem = {
  aad_id: string;
  formulation: string;
  action_verb: string;
  disciplinary_concept: string;
  source_pages: number[];
  course_grounding: string;
};

@Component({
  selector: 'app-identify',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './identify.html',
  styleUrl: './identify.css',
})
export class Identify implements OnInit {
  subjectId = '';

  files: File[] = [];
  loading = false;
  error = '';
  selectionMessage = '';
  selectionError = '';
  savingSelection = false;
  selectionSaved = false;
  selectedAadIds = new Set<string>();
  aads: AADItem[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private formationService: FormationService,
    private changeDetector: ChangeDetectorRef,
  ) {
    this.subjectId = this.route.snapshot.paramMap.get('id') ?? '';
  }

  ngOnInit(): void {
    // A previous long-running request may have completed after the browser
    // disconnected. Always restore the last persisted result on page load.
    this.loading = false;
    this.formationService.getGeneratedAADs(this.subjectId).subscribe({
      next: (response) => {
        this.aads = response.aads ?? [];
        this.changeDetector.detectChanges();
      },
      error: (err) => {
        if (err.status !== 404) {
          console.error(err);
        }
      },
    });
  }

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.error = '';
    this.aads = [];
    this.resetSelection();

    if (!input.files || input.files.length === 0) {
      this.files = [];
      return;
    }

    this.files = Array.from(input.files);
  }

  async identify() {
    this.error = '';
    this.aads = [];
    this.resetSelection();

    if (this.files.length === 0) {
      this.error = 'Veuillez sélectionner au moins un fichier PDF.';
      return;
    }

    this.loading = true;

    try {
      const form = new FormData();
      this.files.forEach((file) => form.append('files', file));
      form.append('subject_id', this.subjectId);

      const response = await fetch('/api/identify', {
        method: 'POST',
        body: form,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error ?? `Erreur HTTP ${response.status}`);
      }
      this.aads = data.aads ?? [];
    } catch (error) {
      console.error(error);
      this.error = error instanceof Error
        ? error.message
        : "Erreur pendant la génération des AAD.";
    } finally {
      this.loading = false;
      this.changeDetector.detectChanges();
    }
  }

  toggleAAD(aadId: string, checked: boolean): void {
    if (checked) {
      this.selectedAadIds.add(aadId);
    } else {
      this.selectedAadIds.delete(aadId);
    }
    this.selectionSaved = false;
    this.selectionMessage = '';
    this.selectionError = '';
  }

  isSelected(aadId: string): boolean {
    return this.selectedAadIds.has(aadId);
  }

  async saveSelection(): Promise<void> {
    const selectedAads = this.aads.filter((aad) => this.selectedAadIds.has(aad.aad_id));
    this.selectionMessage = '';
    this.selectionError = '';
    this.selectionSaved = false;

    if (selectedAads.length === 0) {
      this.selectionError = 'Sélectionnez au moins un AAD pertinent.';
      return;
    }

    this.savingSelection = true;
    try {
      const response = await fetch(
        `/api/aad/${encodeURIComponent(this.subjectId)}/selection`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ aads: selectedAads }),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error ?? `Erreur HTTP ${response.status}`);
      }
      this.selectionSaved = true;
      this.selectionMessage = data.message;
    } catch (error) {
      console.error(error);
      this.selectionError = error instanceof Error
        ? error.message
        : "Impossible d'enregistrer la sélection.";
    } finally {
      this.savingSelection = false;
      this.changeDetector.detectChanges();
    }
  }

  downloadSelection(): void {
    window.location.href = `/api/aad/${encodeURIComponent(this.subjectId)}/selection/download`;
  }

  private resetSelection(): void {
    this.selectedAadIds.clear();
    this.selectionMessage = '';
    this.selectionError = '';
    this.selectionSaved = false;
  }

  back() {
    this.router.navigate(['/subject', this.subjectId]);
  }
}

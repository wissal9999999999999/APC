import { AfterViewInit, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { FormationService } from '../../services/formation';

@Component({
  selector: 'app-responsable-formation',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './responsableformation.html',
  styleUrl: './responsableformation.css',
})
export class ResponsableFormation implements OnInit {

  formationId = '';

  savoirAgirList: any[] = [];
  jalonsList: any[] = [];

  selectedSavoirAgirId: number | null = null;
  selectedJalonId: number | null = null;

  newAC: string = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private formationService: FormationService,
      private cdr: ChangeDetectorRef
  ) {
    this.formationId =
      this.route.snapshot.paramMap.get('formationId') ?? '';
  }

  
  ngAfterContentChecked(): void {
  }

  ngOnInit(): void {
    this.loadSavoirAgir();
  }

  // 🔹 Load all savoir-agir
  loadSavoirAgir(): void {
    this.formationService.getSavoirAgir()
      .subscribe({
        next: (data) => {
          this.savoirAgirList = data;
           this.cdr.detectChanges();
          console.log(this.savoirAgirList);
        },
        error: (err) => console.error(err)
      });
  }

  // 🔹 When savoir changes, load jalons
  onSavoirChange(): void {

    if (!this.selectedSavoirAgirId) {
      this.jalonsList = [];
      return;
    }

    this.formationService
      .getJalons(this.selectedSavoirAgirId.toString())
      .subscribe({
        next: (data) => {
          this.jalonsList = data;
        },
        error: (err) => console.error(err)
      });
  }

  // 🔹 Add AC
  addAC(): void {

    if (!this.selectedSavoirAgirId ||
        !this.selectedJalonId ||
        !this.newAC.trim()) {

      alert("Veuillez remplir tous les champs.");
      return;
    }

    const payload = {
      savoir_agir_id: this.selectedSavoirAgirId,
      jalon_id: this.selectedJalonId,
      ac_text: this.newAC.trim()
    };

    this.formationService.saveAC(payload)
      .subscribe({
        next: () => {
          alert("AC enregistré !");
          this.newAC = '';
        },
        error: (err) => {
          console.error(err);
          alert("Erreur lors de l'enregistrement");
        }
      });
  }

  // 🔹 Generate full JSON from backend
  generateAndDownloadJSON(): void {

    this.formationService
      .exportFormation(this.formationId)
      .subscribe({
        next: (response) => {
          alert("Fichier généré avec succès !");
          console.log(response);
        },
        error: (err) => {
          console.error(err);
          alert("Erreur génération fichier");
        }
      });
  }

  trackById(index: number, item: any): number {
  return item.id;
}

  back(): void {
    this.router.navigate(['/metier', this.formationId]);
  }
}
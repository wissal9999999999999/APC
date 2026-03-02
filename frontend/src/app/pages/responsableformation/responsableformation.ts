import { Component, OnInit } from '@angular/core';
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

  selectedSavoirAgirId: string = '';
  selectedJalonId: string = '';
  newAC: string = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private formationService: FormationService
  ) {
    this.formationId =
      this.route.snapshot.paramMap.get('formationId') ?? '';
  }

  ngOnInit(): void {
    this.loadSavoirAgir();
  }

  loadSavoirAgir(): void {
    this.formationService.getSavoirAgir()
      .subscribe({
        next: (data) => this.savoirAgirList = data,
        error: (err) => console.error(err)
      });
  }

  onSavoirChange(): void {

    if (!this.selectedSavoirAgirId) {
      this.jalonsList = [];
      return;
    }

    this.formationService
      .getJalons(this.selectedSavoirAgirId)
      .subscribe({
        next: (data) => this.jalonsList = data,
        error: (err) => console.error(err)
      });
  }

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

  back(): void {
    this.router.navigate(['/metier', this.formationId]);
  }
}
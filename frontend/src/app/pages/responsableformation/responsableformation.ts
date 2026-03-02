import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-responsable-formation',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './responsableformation.html',
  styleUrl: './responsableformation.css',
})
export class ResponsableFormation {
  formationId = '';

  // champs de saisie
  newSavoirAgir = '';
  newJalon = '';
  newAC = '';

  // données (prototype local)
  savoirAgir: string[] = [];
  jalons: string[] = [];
  acs: string[] = [];

  constructor(private route: ActivatedRoute, private router: Router) {
    this.formationId = this.route.snapshot.paramMap.get('formationId') ?? '';
  }

  // --- AJOUTS ---

  addSavoirAgir() {
    if (!this.newSavoirAgir.trim()) return;
    this.savoirAgir.push(this.newSavoirAgir.trim());
    this.newSavoirAgir = '';
  }

  addJalon() {
    if (!this.newJalon.trim()) return;
    this.jalons.push(this.newJalon.trim());
    this.newJalon = '';
  }

  addAC() {
    if (!this.newAC.trim()) return;
    this.acs.push(this.newAC.trim());
    this.newAC = '';
  }

  // --- NAVIGATION ---

  back() {
    this.router.navigate(['/metier', this.formationId]);
  }
}

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

type RoleItem = {
  id: 'resp-formation' | 'resp-ec';
  title: string;
  subtitle: string;
};

@Component({
  selector: 'app-metier',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './metier.html',
  styleUrl: './metier.css',
})
export class Metier {
  formationId = '';

  roles: RoleItem[] = [
    {
      id: 'resp-formation',
      title: 'Responsable de formation',
      subtitle: 'Gérer savoir-agir, jalons, et apprentissages critiques (AC).',
    },
    {
      id: 'resp-ec',
      title: 'Responsable EC',
      subtitle: 'Accéder aux matières : Alignement AC→AAD et Identification des AAD.',
    },
  ];

  constructor(private route: ActivatedRoute, private router: Router) {
    this.formationId = this.route.snapshot.paramMap.get('formationId') ?? '';
  }

  selectRole(roleId: RoleItem['id']) {
    if (roleId === 'resp-ec') {
      // ✅ branche vers ton flux existant
      this.router.navigate(['/subjects'], {
        queryParams: { formation: this.formationId },
      });
      return;
    }

    // ✅ on créera cette partie après
    this.router.navigate(['/responsable-formation', this.formationId]);
  }

  back() {
    this.router.navigate(['/formation']);
  }
}

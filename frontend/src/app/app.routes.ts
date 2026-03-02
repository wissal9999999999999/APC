import { Routes } from '@angular/router';

// nouvelle page
import { Formation } from './pages/formation/formation';
import { Metier } from './pages/metier/metier';


// (tes pages existantes)
import { Subjects } from './pages/subjects/subjects';
import { SubjectMenu } from './pages/subject-menu/subject-menu';
import { Align } from './pages/align/align';
import { Identify } from './pages/identify/identify';
import { ResponsableFormation } from './pages/responsableformation/responsableformation';

export const routes: Routes = [
  //  page d'accueil -> formation
  { path: '', pathMatch: 'full', redirectTo: 'formation' },

  { path: 'formation', component: Formation },
  { path: 'metier/:formationId', component: Metier },
  { path: 'responsable-formation/:formationId', component: ResponsableFormation },


  // (on ajoutera /metier à l’étape suivante)
  // { path: 'metier/:formationId', component: Metier },

  //  ta partie existante (Responsable EC)
  { path: 'subjects', component: Subjects },
  { path: 'subject/:id', component: SubjectMenu },
  { path: 'subject/:id/align', component: Align },
  { path: 'subject/:id/identify', component: Identify },

  // fallback
  { path: '**', redirectTo: 'formation' },
];

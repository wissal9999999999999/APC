import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-subject-menu',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './subject-menu.html',
  styleUrl: './subject-menu.css',
})
export class SubjectMenu {
  subjectId = '';

  constructor(private route: ActivatedRoute, private router: Router) {
    this.subjectId = this.route.snapshot.paramMap.get('id') ?? '';
  }

  goAlign() {
    this.router.navigate(['/subject', this.subjectId, 'align']);
  }

  goIdentify() {
  this.router.navigate(['/subject', this.subjectId, 'identify']);
}


  back() {
    this.router.navigate(['/subjects']);
  }

  
}

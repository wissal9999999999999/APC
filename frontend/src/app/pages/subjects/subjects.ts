import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-subjects',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './subjects.html',
  styleUrl: './subjects.css',
})
export class Subjects {
  constructor(private router: Router) {}

  go(id: string) {
    this.router.navigate(['/subject', id]);
  }
}

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubjectMenu } from './subject-menu';

describe('SubjectMenu', () => {
  let component: SubjectMenu;
  let fixture: ComponentFixture<SubjectMenu>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SubjectMenu]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SubjectMenu);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Identify } from './identify';

describe('Identify', () => {
  let component: Identify;
  let fixture: ComponentFixture<Identify>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Identify]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Identify);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

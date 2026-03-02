import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Align } from './align';

describe('Align', () => {
  let component: Align;
  let fixture: ComponentFixture<Align>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Align]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Align);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

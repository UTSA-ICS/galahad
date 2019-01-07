import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ValorsDashboardComponent } from './valors-dashboard.component';

describe('ValorsDashboardComponent', () => {
  let component: ValorsDashboardComponent;
  let fixture: ComponentFixture<ValorsDashboardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ValorsDashboardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ValorsDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TransducerDashboardComponent } from './transducer-dashboard.component';

describe('TransducerDashboardComponent', () => {
  let component: TransducerDashboardComponent;
  let fixture: ComponentFixture<TransducerDashboardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TransducerDashboardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TransducerDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

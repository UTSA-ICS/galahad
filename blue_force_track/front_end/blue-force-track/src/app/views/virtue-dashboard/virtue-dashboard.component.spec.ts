import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VirtueDashboardComponent } from './virtue-dashboard.component';

describe('VirtueDashboardComponent', () => {
  let component: VirtueDashboardComponent;
  let fixture: ComponentFixture<VirtueDashboardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VirtueDashboardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VirtueDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApplicationDashboardComponent } from './application-dashboard.component';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {TableModule} from 'primeng/table';

@NgModule({
  imports: [
    CommonModule,
    NgxChartsModule,
    TableModule
  ],
  exports: [
    ApplicationDashboardComponent
  ],
  declarations: [ApplicationDashboardComponent]
})
export class ApplicationDashboardModule { }

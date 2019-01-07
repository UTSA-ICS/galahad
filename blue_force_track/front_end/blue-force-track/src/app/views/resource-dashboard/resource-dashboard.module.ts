import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResourceDashboardComponent } from './resource-dashboard.component';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {TableModule} from 'primeng/table';

@NgModule({
  imports: [
    CommonModule,
    NgxChartsModule,
    TableModule
  ],
  exports: [
    ResourceDashboardComponent
  ],
  declarations: [ResourceDashboardComponent]
})
export class ResourceDashboardModule { }

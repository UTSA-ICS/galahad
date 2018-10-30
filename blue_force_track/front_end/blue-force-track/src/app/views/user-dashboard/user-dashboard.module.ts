import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserDashboardComponent } from './user-dashboard.component';
import {NgxChartsModule} from '@swimlane/ngx-charts';
import {TableModule} from 'primeng/table';

@NgModule({
  imports: [
    CommonModule,
    NgxChartsModule,
    TableModule
  ],
  exports: [
    UserDashboardComponent
  ],
  declarations: [UserDashboardComponent]
})
export class UserDashboardModule { }

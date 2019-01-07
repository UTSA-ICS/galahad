import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule} from '@angular/common/http';

// PrimeNG Imports
import {MenuModule} from 'primeng/menu';
import {TableModule} from 'primeng/table';

import { AppComponent } from './app.component';
import { AppRoutes } from './app.routes';

// Visualization Imports
import { NgxChartsModule } from '@swimlane/ngx-charts';



// App Imports
import { ValorsDashboardModule } from './views/valors-dashboard/valors-dashboard.module';
import { ApplicationDashboardModule } from './views/application-dashboard/application-dashboard.module';
import { ResourceDashboardModule } from './views/resource-dashboard/resource-dashboard.module';
import { RoleDashboardModule } from './views/role-dashboard/role-dashboard.module';
import { TransducerDashboardModule } from './views/transducer-dashboard/transducer-dashboard.module';
import { UserDashboardModule } from './views/user-dashboard/user-dashboard.module';
import { VirtueDashboardModule } from './views/virtue-dashboard/virtue-dashboard.module';
import { ReadmeComponent } from './views/readme/readme.component';

@NgModule({
  declarations: [
    AppComponent,
    ReadmeComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MenuModule,
    AppRoutes,
    HttpClientModule,
    ValorsDashboardModule,
    ApplicationDashboardModule,
    ResourceDashboardModule,
    RoleDashboardModule,
    TransducerDashboardModule,
    UserDashboardModule,
    VirtueDashboardModule,
    NgxChartsModule,
    TableModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }

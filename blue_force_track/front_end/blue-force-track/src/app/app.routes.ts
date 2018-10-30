import { Routes, RouterModule } from '@angular/router';
import { ModuleWithProviders } from '@angular/core';
import { ValorsDashboardComponent } from './views/valors-dashboard/valors-dashboard.component';
import { VirtueDashboardComponent} from './views/virtue-dashboard/virtue-dashboard.component';
import { UserDashboardComponent } from './views/user-dashboard/user-dashboard.component';
import { TransducerDashboardComponent } from './views/transducer-dashboard/transducer-dashboard.component';
import { RoleDashboardComponent } from './views/role-dashboard/role-dashboard.component';
import { ResourceDashboardComponent } from './views/resource-dashboard/resource-dashboard.component';
import { ApplicationDashboardComponent } from './views/application-dashboard/application-dashboard.component';

export const routes: Routes = [
  { path: 'views/valors-dashboard', component: ValorsDashboardComponent },
  { path: 'views/application-dashboard', component: ApplicationDashboardComponent },
  { path: 'views/resource-dashboard', component: ResourceDashboardComponent },
  { path: 'views/role-dashboard', component: RoleDashboardComponent },
  { path: 'views/transducer-dashboard', component: TransducerDashboardComponent },
  { path: 'views/user-dashboard', component: UserDashboardComponent },
  { path: 'views/valors-dashboard', component: ValorsDashboardComponent },
  { path: 'views/virtue-dashboard', component: VirtueDashboardComponent }
];

export const AppRoutes: ModuleWithProviders = RouterModule.forRoot(routes);

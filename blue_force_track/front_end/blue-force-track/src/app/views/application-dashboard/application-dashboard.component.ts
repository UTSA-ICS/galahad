import { Component, OnInit } from '@angular/core';
import {DataService} from '../../services/data.service';

@Component({
  selector: 'app-application-dashboard',
  templateUrl: './application-dashboard.component.html',
  styleUrls: ['./application-dashboard.component.css']
})
export class ApplicationDashboardComponent implements OnInit {

  // Table Config
  cols = [
    { field: 'name', header: 'Name' },
    { field: 'cos', header: 'OS' },
    { field: 'controls', header: 'Controls'}
  ];

  tableData: any[];

  constructor(private dataService: DataService) { }

  ngOnInit() {
    this.dataService.getApplications().subscribe(
      applications => (
        this.tableData = applications
      ));
  }

}

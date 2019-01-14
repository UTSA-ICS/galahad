import { Component, OnInit } from '@angular/core';
import {DataService} from '../../services/data.service';

@Component({
  selector: 'app-resource-dashboard',
  templateUrl: './resource-dashboard.component.html',
  styleUrls: ['./resource-dashboard.component.css']
})
export class ResourceDashboardComponent implements OnInit {

  // Table Config
  cols = [
    { field: 'cid', header: 'Id'},
    { field: 'ctype', header: 'Type' },
    { field: 'cunc', header: 'Path' },
    { field: 'ccredentials', header: 'Credentials' }
  ];

  tableData: any[];

  constructor(private dataService: DataService) { }

  ngOnInit() {
    this.dataService.getResources().subscribe(
      resources => (
        this.tableData = resources
      ));
  }

}

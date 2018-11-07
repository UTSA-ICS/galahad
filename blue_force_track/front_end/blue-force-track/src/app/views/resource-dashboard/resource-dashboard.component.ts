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
    { field: 'dn', header: 'Domain Name' },
    { field: 'ou', header: 'Organizational Unit' },
    { field: 'ccredentials', header: 'Credentials' },
    { field: 'cunc', header: 'Path' },
    { field: 'ctype', header: 'Type' },
    { field: 'cid', header: 'Id'}
  ];

  tableData: any[];

  constructor(private dataService: DataService) { }

  ngOnInit() {
    this.dataService.getResources().subscribe(
      resources => (
        this.tableData = resources
      ));

    // this.tableData = [
    //   {
    //     dn: '"cid=fileshare1,cn=resources,ou=virtue,dc=canvas,dc=virtue,dc=com"',
    //     ou: 'virtue',
    //     cid: 'fileshare1',
    //     ccredentials: 'token',
    //     cunc: '//172.30.1.250/VirtueFileShare',
    //     ctype: 'DRIVE'
    //   }
    // ];
  }

}

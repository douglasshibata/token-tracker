import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { LogsService } from '../../core/services/logs.service';
import { of } from 'rxjs';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let logsService: LogsService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DashboardComponent ],
      imports: [ HttpClientTestingModule ],
      providers: [ LogsService ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    logsService = TestBed.inject(LogsService);
    spyOn(logsService, 'getStats').and.returnValue(of({ total_spend: 10, total_tokens: 100, blocked_count: 1 }));
    fixture.detectChanges();
  });

  it('should create and load stats', () => {
    expect(component).toBeTruthy();
    expect(component.stats.total_spend).toBe(10);
  });
});

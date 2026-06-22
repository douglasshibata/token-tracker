import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { BudgetService } from './budget.service';

describe('BudgetService', () => {
  let service: BudgetService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [BudgetService]
    });
    service = TestBed.inject(BudgetService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should fetch limits', () => {
    const mockLimits = { daily_limit: 10 };
    service.getLimits('123').subscribe(limits => {
      expect(limits.daily_limit).toBe(10);
    });

    const req = httpMock.expectOne('/v1/projects/123');
    expect(req.request.method).toBe('GET');
    req.flush(mockLimits);
  });
});

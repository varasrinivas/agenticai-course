import { IsInt, IsOptional, IsString, Length, Min } from 'class-validator';

/**
 * Validates the inbound prior auth request before we forward it.
 * Mirrors PriorAuthRequest in @um-lite/domain (kept inline here so the
 * service stays runnable before the workspace path mapping is wired).
 */
export class CreatePriorAuthDto {
  @IsString() @Length(1, 32)
  memberId!: string;

  @IsString() @Length(1, 32)
  providerId!: string;

  @IsString() @Length(3, 10)
  procedureCode!: string;

  @IsString() @Length(3, 10)
  diagnosisCode!: string;

  @IsInt() @Min(1)
  requestedUnits!: number;

  @IsOptional() @IsString() @Length(0, 2000)
  notes?: string;
}

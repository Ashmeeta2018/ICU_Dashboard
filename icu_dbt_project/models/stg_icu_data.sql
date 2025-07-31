select
    Date,
    PatientID,
    Unit,
    BedOccupancy,
    PatientCensus,
    VentilatorUtilization,
    LengthOfStay,
    AcuityLevel,
    AdmissionSource,
    VentilatorStatus
from {{ source('main', 'icu_data') }}

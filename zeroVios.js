const ERROR_FILTERS = [
  {
    name: 'SEQUENTIAL ID BREAK WARNING',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'SEQUENTIAL ID BREAK WARNING',
    key: 'sequentialIdBreak'
  },
  {
    name: 'ENGINE HOURS HAVE CHANGED AFTER SHUT DOWN WARNING',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'ENGINE HOURS HAVE CHANGED AFTER SHUT DOWN WARNING',
    key: 'engineHoursAfterShutdown'
  },
  {
    name: 'ODOMETER ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'ODOMETER ERROR',
    key: 'odometerError'
  },
  {
    name: 'DIAGNOSTIC EVENT',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'DIAGNOSTIC EVENT',
    key: 'diagnosticEvent'
  },
  { 
    name: 'LOCATION CHANGED ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'LOCATION CHANGED ERROR',
    key: 'locationChangedError'
  },
  { 
    name: 'INCORRECT INTERMEDIATE PLACEMENT ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'INCORRECT INTERMEDIATE PLACEMENT ERROR',
    key: 'incorrectIntermediatePlacementError'
  },
  { 
    name: 'ENGINE HOURS WARNING',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'ENGINE HOURS WARNING',
    key: 'engineHoursWarning'
  },
  { 
    name: 'NO SHUT DOWN ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'NO SHUT DOWN ERROR',
    key: 'noShutdownError'
  },
  { 
    name: 'EXCESSIVE LOG IN WARNING',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'EXCESSIVE LOG IN WARNING',
    key: 'excessiveLogInWarning'
  },
  { 
    name: 'EXCESSIVE LOG OUT WARNING',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'EXCESSIVE LOG OUT WARNING',
    key: 'excessiveLogOutWarning'
  },
  { 
    name: 'TWO IDENTICAL STATUSES ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'TWO IDENTICAL STATUSES ERROR',
    key: 'twoIdenticalStatusesError'
  },
  { 
    name: 'DRIVING ORIGIN WARNING',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'DRIVING ORIGIN WARNING',
    key: 'drivingOriginWarning'
  },
  { 
    name: 'NO DATA IN ODOMETER OR ENGINE HOURS ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'NO DATA IN ODOMETER OR ENGINE HOURS ERROR',
    key: 'noDataInOdometerOrEngineHours'
  },
  { 
    name: 'LOCATION ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'LOCATION ERROR',
    key: 'locationError'
  },
  { 
    name: 'LOCATION DID NOT CHANGE WARNING',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'LOCATION DID NOT CHANGE WARNING',
    key: 'locationDidNotChangeWarning'
  },
  { 
    name: 'MISSING INTERMEDIATE ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'MISSING INTERMEDIATE ERROR',
    key: 'missingIntermediateError'
  },
  {
    name: 'INCORRECT STATUS PLACEMENT ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'INCORRECT STATUS PLACEMENT ERROR',
    key: 'incorrectStatusPlacementError'
  },
  {
    name: 'THE SPEED WAS MUCH HIGHER THAN THE SPEED LIMIT IN',
    match: (errorMessage) => errorMessage && errorMessage.trim().startsWith('THE SPEED WAS MUCH HIGHER THAN THE SPEED LIMIT IN'),
    key: 'speedMuchHigherThanLimit'
  },
  {
    name: 'THE SPEED WAS HIGHER THAN THE SPEED',
    match: (errorMessage) => errorMessage && errorMessage.trim().startsWith('THE SPEED WAS HIGHER THAN THE SPEED'),
    key: 'speedHigherThanLimit'
  },
  {
    name: 'EVENT HAS MANUAL LOCATION',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'EVENT HAS MANUAL LOCATION',
    key: 'eventHasManualLocation'
  },
  {
    name: 'NO POWER UP ERROR',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'NO POWER UP ERROR',
    key: 'noPowerUpError'
  },
  {
    name: 'UNIDENTIFIED DRIVER EVENT',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'UNIDENTIFIED DRIVER EVENT',
    key: 'unidentifiedDriverEvent'
  },
  {
    name: 'EVENT IS NOT DOWNLOADED',
    match: (errorMessage) => errorMessage && errorMessage.trim() === 'EVENT IS NOT DOWNLOADED',
    key: 'eventIsNotDownloaded'
  },
];
export interface User {
  id: string
  display_name: string
}

export interface Household {
  id: string
  name: string
}

export interface HouseholdMe {
  household: Household | null
  members: User[]
}

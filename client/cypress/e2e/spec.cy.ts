describe('visit home page', () => {
  it('passes', () => {
    cy.visit('http://localhost:5173')
  })
})

describe('visit about page', () => {
    it('passes', () => {
        cy.visit('http://localhost:5173/about')
    })
})

describe('visit contact page', () => {
    it('passes', () => {
        cy.visit('http://localhost:5173/contact')
    })
})

describe('visit login page', () => {
    it('passes', () => {
        cy.visit('http://localhost:5173/login')
    })
})

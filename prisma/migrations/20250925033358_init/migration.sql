-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "email" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Item" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "plaidItemId" TEXT NOT NULL,
    "accessToken" TEXT NOT NULL,
    "institutionId" TEXT,
    "transactionsCursor" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Item_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Account" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "itemId" TEXT NOT NULL,
    "plaidAccountId" TEXT NOT NULL,
    "name" TEXT,
    "officialName" TEXT,
    "mask" TEXT,
    "type" TEXT,
    "subtype" TEXT,
    "availableBalance" DECIMAL,
    "currentBalance" DECIMAL,
    "currency" TEXT DEFAULT 'USD',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Account_itemId_fkey" FOREIGN KEY ("itemId") REFERENCES "Item" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Transaction" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "accountId" TEXT NOT NULL,
    "plaidTransactionId" TEXT NOT NULL,
    "name" TEXT,
    "merchantName" TEXT,
    "amount" DECIMAL NOT NULL,
    "isoCurrencyCode" TEXT DEFAULT 'USD',
    "date" DATETIME NOT NULL,
    "authorizedDate" DATETIME,
    "pending" BOOLEAN NOT NULL DEFAULT false,
    "category" JSONB,
    "location" JSONB,
    "paymentChannel" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Transaction_accountId_fkey" FOREIGN KEY ("accountId") REFERENCES "Account" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "Item_plaidItemId_key" ON "Item"("plaidItemId");

-- CreateIndex
CREATE UNIQUE INDEX "Account_plaidAccountId_key" ON "Account"("plaidAccountId");

-- CreateIndex
CREATE UNIQUE INDEX "Transaction_plaidTransactionId_key" ON "Transaction"("plaidTransactionId");

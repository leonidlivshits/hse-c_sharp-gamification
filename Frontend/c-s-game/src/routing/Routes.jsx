import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import Home from "../pages/HomePage/HomePage";
import Materials from "../pages/Materials/Materials";
import Tests from "../pages/Tests/Tests";
import PersonalAccount from "../pages/PersonalAccount/PersonalAccount";
import NoPage from "../pages/NoPage/NoPage";
import MaterialDetails from "../pages/Materials/MaterialsDetails";
import Analytics from "../pages/PersonalAccount/Analytics";

import {
    MAIN_ROUTE,
    MATERIALS_ROUTE,
    TESTS_ROUTE,
    PERSONAL_ACCOUNT_ROUTE,
    NO_PAGE_ROUTE,
    MATERIAL_DETAILS_ROUTE,
    ANALYTICS_ROUTE
} from "./const.js";

const AppRouter = () => {
  return (
    <Routes>
      <Route path={MAIN_ROUTE} element={<Home />} />
      <Route path={MATERIALS_ROUTE} element={<Materials />} />
      <Route path={TESTS_ROUTE} element={<Tests />} />
      <Route path={PERSONAL_ACCOUNT_ROUTE} element={<PersonalAccount />} />
      <Route path={NO_PAGE_ROUTE} element={<NoPage />} />
      <Route path={MATERIAL_DETAILS_ROUTE} element={<MaterialDetails />} />
      <Route path={ANALYTICS_ROUTE} element={<Analytics />} />
      <Route path="*" element={<Navigate to={NO_PAGE_ROUTE} />} />
    </Routes>
  );
};

export default AppRouter;